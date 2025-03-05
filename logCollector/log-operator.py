import kopf
import kubernetes.client
from kubernetes import config
from minio import Minio
import time
import logging
import urllib3
import io

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load kubeconfig (for local dev) or use in-cluster config
try:
    config.load_kube_config()
except:
    config.load_incluster_config()

v1 = kubernetes.client.CoreV1Api()

# Handler for when a LogCollector CR is created or updated
@kopf.on.create('local.com', 'v1', 'logcollectors')
@kopf.on.update('local.com', 'v1', 'logcollectors')
def handle_logcollector(spec, name, namespace, **kwargs):

    logging.info(f"Handling LogCollector {name} in {namespace}")

    # Extract spec fields
    pod_selector = spec.get('podSelector')
    bucket = spec.get('bucket')
    minio_endpoint = spec.get('minioEndpoint')
    access_key = spec.get('accessKey')
    secret_key = spec.get('secretKey')
    debug_mode = spec.get('debug', False)
    rewrite = spec.get('rewrite', False)
    push_interval = spec.get('pushInterval', 60)

    # Initialize Minio client
    if debug_mode == "true":
        print(f"Connecting to Minio at {minio_endpoint} with access key {access_key}")
        debug = True
    if rewrite == "true":
        print(f"Rewriting logs to include pod name")
        rewrite = True
    minio_client = Minio(
        minio_endpoint.replace("https://", "").replace("http://", ""),
        access_key=access_key,
        secret_key=secret_key,
        cert_check=False
    )

    # Ensure bucket exists
    if not minio_client.bucket_exists(bucket):
        if debug:
            logging.debug(f"Creating bucket {bucket}")
        minio_client.make_bucket(bucket)

    # Infinite loop to periodically collect logs
    while True:
        try:
            # List pods matching the selector
            pods = v1.list_namespaced_pod(
                namespace,
                label_selector=pod_selector
            ).items

            for pod in pods:
                pod_name = pod.metadata.name
                log_data = v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=namespace
                )

                # Rewrite logs to include pod name as prefix
                if rewrite:
                    if debug:
                        logging.debug(f"Rewriting logs for {pod_name}")
                    list_files = minio_client.list_objects(bucket)
                    for log in list_files:
                        if log.object_name.startswith(pod_name):
                            if debug:
                                logging.debug(f"Deleting existing log {log.object_name}")
                            minio_client.remove_object(bucket, log.object_name)

                # Upload logs to Minio
                object_name = f"{pod_name}-{int(time.time())}.log"
                print(f"Uploading logs for {pod_name} to {bucket}/{object_name}")
                minio_client.put_object(
                    bucket,
                    object_name,
                    data=io.BytesIO(log_data.encode('utf-8')),
                    length=len(log_data)
                )
                logging.info(f"Uploaded logs for {pod_name} to {bucket}/{object_name}")

            # Wait before next collection (e.g., 60 seconds)
            time.sleep(push_interval)

        except Exception as e:
            logging.error(f"Error processing logs: {e}")
            time.sleep(10)  # Retry after delay


# Run the operator
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    kopf.run()