build: 
    docker build -t gcr.io/datacenter-293401/rest-app:v1 .

push: 
    docker push gcr.io/datacenter-293401/rest-app:v1

run: 
    docker run --rm gcr.io/datacenter-293401/rest-app:v1

rest-deployment:
    kubectl apply -f rest-deployment.yaml

rest-service:
    kubectl apply -f rest-service.yaml

rest-ingress:
    kubectl apply -f rest-ingress.yaml

default: build