import aiodocker
import aioftp
import os
import subprocess
from aiohttp import web
from gcloud import storage, resource_manager
from pathlib import Path
import asyncio
import aiojobs
from aiojobs.aiohttp import setup, spawn
from multidict import MultiDict
from select import select
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

host = "localhost"
ftp_user = "bob"
ftp_password = "12345"
folder = Path().absolute()
status = 'IDLE'

routes = web.RouteTableDef()


# con = ftplib.FTP(host=host, user=ftp_user, passwd=ftp_password)


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
    global status
    status = "Files downloading"
    async with aioftp.ClientSession(host=host, user=ftp_user, password=ftp_password) as client:
        for path, info in (await client.list()):
            await client.download(path, destination="./Work/pipeline/" + path.name, write_into=True)


async def model_training():
    global status
    status = "Model training."
    await asyncio.create_subprocess_shell('Rscript /home/vyachap/Work/pipeline/estimate_models.R '
                                          '--booked /home/vyachap/Work/pipeline/md.csv '
                                          '--cogs /home/vyachap/Work/pipeline/mdcogs.csv')


async def build_image():
    global status
    status = "Image building."
    docker = aiodocker.Docker()
    # Add a real path to Dockerfile in r-project-service.
    await docker.images.build(path_dockerfile='./r-driveproject/Dockerfile', tag='lol:kek', rm=True)


@routes.get('/status')
async def status_endpoint(request):
    global status
    return web.Response(text=status)


async def upload_csv(request):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket("ad_documents")
    blob = bucket.blob('/chosen-path-to-object/{name-of-object}')
    blob.upload_from_filename('D:/Download/02-06-53.pdf')


async def upload_model(request):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket("ad_documents")
    blob = bucket.blob('/chosen-path-to-object/{name-of-object}')
    blob.upload_from_filename('D:/Download/02-06-53.pdf')


async def upload_image():
    pass


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


async def start():
    global status
    try:
        await download_csv()
    except Exception as e:
        status = 'FAILED'
        return web.Response(text="Download failed. Reason: {}".format(e), status=500)
    try:
        await model_training()
    except Exception as e:
        status = 'FAILED'
        return web.Response(text="R-model training failed. Reason: {}".format(e), status=500)
    # upload_csv()
    # upload_model()
    try:
        await build_image()
    except Exception as e:
        status = 'FAILED'
        return web.Response(text="Image building failed. Reason: {}".format(e), status=500)
    # upload_image()


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


app = web.Application()
app.add_routes(routes)
setup(app)
web.run_app(app)
