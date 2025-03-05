# Kube log operator

This is a training project.
The goal is writing kubernetes operator which push logs to S3 (MinIO)

## PREREQUIRENMENTS
1. Python 3
2. Minikube
3. Minio
4. Minio console (mc)
5. Pip packages:
kopf: For building the operator.
kubernetes: Python client for interacting with Kubernetes.
minio: Python client for Minio.

 ```
pip install kopf kubernetes minio
```

## Install Minio operator

```
helm repo add minio-operator https://operator.min.io

helm search repo minio-operator

helm show values minio-operator/operator > minio-values.yaml

helm install \
  --namespace minio-operator \
  --create-namespace \
  -f minio-values.yaml \
  operator minio-operator/operator

kubectl get all -n minio-operator

```
## Install Minio tenant

```
curl -sLo tenant-values.yaml https://raw.githubusercontent.com/minio/operator/master/helm/tenant/values.yaml
```

Fix values and deploy
```
helm install \
--namespace tenant-namespace \
--create-namespace \
--values tenant-values.yaml \
tenant1 minio-operator/tenant
```



Forward the Tenant’s MinIO port,
Create an alias for the Tenant service,
You can use mc mb to create a bucket on the Tenant:

```
kubectl port-forward svc/minio-tenant-hl 9000 -n tenant-namespace
mc alias set myminio https://localhost:9000 minio minio123 --insecure
mc mb myminio/mybucket --insecure

mc ls myminio/mybucketmybucket
```

When MinIO started we can setup operator resources:

```
cd kube
kubectl apply -f rbac.yaml
kubectl apply -f logcollector-crd.yaml
# Check parameters in logcollector-sample.yaml
kubectl apply -f logcollector-sample.yaml
```

Test your connection:

```
cd ..
python3 minio-test-connection.py
```

If you see no errors then deploy operator:

```
kubectl apply -f logcollector-deployment.yaml
```

