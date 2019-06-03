import docker
import ftplib
import os
import subprocess
from aiohttp import web
from gcloud import storage


host = "localhost"
ftp_user = "bob"
ftp_password = "12345"
folder = '/home/vyachap/PycharmProjects/Echo/Files'

routes = web.RouteTableDef()

con = ftplib.FTP(host=host, user=ftp_user, passwd=ftp_password)

@routes.get('/')
async def handler(request):
    return web.Response()

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
async def download_csv(path: str):
    filenames = con.nlst()
    print("Received list of files")
    for filename in filenames:
        host_file = os.path.join(path, filename)
        try:
            with open(host_file, 'wb') as local_file:
                con.retrbinary('RETR ' + filename, local_file.write)
                print("File {} downloaded". format(filename))
        except ftplib.error_perm:
            pass


async def model_training():
    print("R script is running...")
    subprocess.call(['Rscript', 'estimate_models.R', '--booked', 'md.csv', '--cogs', 'mdcogs.csv'])
    print("R model relearned")


@routes.get('/download')
async def download_endpoint(request):
    try:
        download_csv(folder)
    except Exception as e:
        return web.Response(text="Download Failed. Reason: {}".format(e), status=500)
    return web.Response(text="Download Complete", status=200)


@routes.get('/training')
async def training_endpoint(request):
    try:
        model_training()
    except Exception as e:
        return web.Response(text="R-model training failed. Reason: {}".format(e), status=500)
    return web.Response(text="R-model trained successfully", status=200)


async def build_image():
    client = docker.APIClient(base_url='unix://var/run/docker.sock')
    image = client.build(dockerfile='/home/vyachap/PycharmProjects/Echo/Dockerfile', rm=True)


@routes.get('/start_pipeline')
async def start_pipeline(request):
    pass


@routes.get('/csv_upload')
async def upload_csv(request):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket("ad_documents")
    blob = bucket.blob('/chosen-path-to-object/{name-of-object}')
    blob.upload_from_filename('D:/Download/02-06-53.pdf')


async def upload_model():
    storage_client = storage.Client()
    bucket = storage_client.get_bucket("ad_documents")
    blob = bucket.blob('/chosen-path-to-object/{name-of-object}')
    blob.upload_from_filename('D:/Download/02-06-53.pdf')


async def upload_image():
    pass

# app = web.Application()
# web.run_app(app)

# build_image()

