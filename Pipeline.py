from datetime import datetime
import aioftp
import os
from aiohttp import web
from pathlib import Path
import asyncio
import aiojobs
from aiojobs.aiohttp import setup, spawn
from multidict import MultiDict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

host = "localhost"
ftp_user = "bob"
ftp_password = "12345"
folder = Path().absolute()
state = {
    'status': 'IDLE',
    'error': None,
    'image_tag' : None
    }

routes = web.RouteTableDef()


pwd = os.path.dirname(os.path.abspath(__file__))


# Loading block
# async def upload_files():
#     files_path = '/home/vyachap/Test Files/'
#     walk = os.walk(files_path)
#     file_list = []
#     for address, dirs, files in walk:
#         file_list = files
#     for file in file_list:
#         f = open(files_path + file, "rb")
#         con.storbinary("STOR " + file, f)


# Downloading block
async def download_csv():
    global state
    error = None
    state['status'] = "Files downloading"
    try:
        async with aioftp.ClientSession(host=host, user=ftp_user, password=ftp_password) as client:
            for path, info in (await client.list()):
                try:
                    await client.download(path, destination=f"{pwd}/r-driveproject/src/data/" + path.name,
                                          write_into=True)
                except Exception as e:
                    state['status'] = 'FAILED'
                    state['error'] = e
                    error = 'CSV download failed'

    except Exception as exc:
        state['status'] = 'FAILED'
        state['error'] = exc
        error = 'Something went wrong with connection to FTP'

    return error


async def model_training():
    global state
    state['status'] = "Model training"
    error = None
    r_script = await asyncio.create_subprocess_shell(f'Rscript {pwd}/estimate_models.R '
                                                     f'--booked {pwd}/md.csv '
                                                     f'--cogs {pwd}/mdcogs.csv '
                                                     f'--output {pwd}/r-driveproject/src/data/',
                                                     stdout=asyncio.subprocess.PIPE,
                                                     stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await r_script.communicate()

    if r_script.returncode != 0:
        state['status'] = 'FAILED'
        state['error'] = stderr.decode()
        error = stderr.decode()

    return error


async def build_image():
    global state
    state['status'] = "Image building"
    error = None
    tag = datetime.now().strftime("%Y%m%d%H%M")
    state['image_tag'] = tag
    image = await asyncio.create_subprocess_shell(f'docker build -t us.gcr.io/synapse-157713/r-demo-project:{tag} {pwd}/r-driveproject')
    stdout, stderr = await image.communicate()

    if image.returncode != 0:
        state['status'] = 'FAILED'
        state['error'] = stderr.decode()
        error = stderr.decode()

    return error


async def upload_image():
    global state
    state['status'] = "Pushing image to Google Cloud Registry"
    error = None
    tag = state['image_tag']
    image_push = await asyncio.create_subprocess_shell(f'gcloud docker -- push us.gcr.io/synapse-157713/r-demo-project:{tag}')
    stdout, stderr = await image_push.communicate()

    if image_push.returncode != 0:
        state['status'] = 'FAILED'
        state['error'] = stderr.decode()
        error = stderr.decode()

    return error


async def start():
    global state
    state['error'] = None
    pipeline = [
        # download_csv,
        # model_training,
        build_image,
        upload_image
    ]
    for func in pipeline:
        if await func() is not None:
            return

    state['status'] = 'IDLE'
    # upload_csv()
    # upload_model()


async def file_upload_handler(request):
    data = await request.post()
    script = data['script']
    filename = script.filename
    script_file = data['script'].file
    content = script_file.read()
    return web.Response(body=content, headers=MultiDict({'CONTENT-DISPOSITION': script_file}))


@routes.get('/')
async def handler(request):
    return web.Response(text='OK')


@routes.post('/training')
async def training_endpoint(request):
    try:
        await model_training()
    except Exception as e:
        return web.Response(text="R-model training failed. Reason: {}".format(e), status=500)
    return web.Response(text="R-model trained successfully", status=200)


@routes.get('/start_pipeline')
async def start_pipeline(request):
    scheduler = await aiojobs.create_scheduler()
    await scheduler.spawn(start())
    return web.Response(text="Pipeline started")


@routes.get('/status')
async def status_endpoint(request):
    global state
    if state['error']:
        return web.Response(text=" Status: {}.\n Error: {}".format(state['status'], state['error']))
    else:
        return web.Response(text=" Status: {}.".format(state['status']))


app = web.Application()
app.add_routes(routes)
setup(app)
web.run_app(app)
