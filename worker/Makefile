build: 
    docker build -t gcr.io/datacenter-293401/worker-app:v1 .

push: 
    docker push gcr.io/datacenter-293401/worker-app:v1

run: 
    docker run --rm gcr.io/datacenter-293401/worker-app:v1

worker-deployment:
    kubectl apply -f worker-deployment.yaml

default: build