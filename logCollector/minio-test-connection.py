from minio import Minio
from minio.error import S3Error
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

minio_client = Minio(
    "localhost:9000",
    access_key="minio",
    secret_key="minio123",
    cert_check=False
    )

try:
    objects = minio_client.list_objects("logs")
    for obj in objects:
        print(obj.object_name)

except S3Error as err:
    print(err)