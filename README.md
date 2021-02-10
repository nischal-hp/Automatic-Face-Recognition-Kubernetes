# Automatic-Face-Recognition-Kubernetes

In this project I implemented Automatic face recognition service using kubernetes.


### The following four containers were deployed which provide the following services :

+ **rest** - The REST frontend will accept images or paths to images for analysis and handle queries concerning specific images. The REST worker will queue tasks to workers using `rabbitmq` messages. 

+ **worker** - Worker nodes will receive work requests to analyze images. If those images contain face data that can be scanned, the information is entered into the REDIS database. 

+ **rabbitmq** - The RabbitMQ deployment and service that acts as the rabbit-mq broker. 

+ **redis** - The Redis deployment and service to provide the redis database server. 

More details about each of the above can be known through the "README.md" files provided in each of the folders.


### Face Recognition
The worker node will use [open source face recognition software](https://github.com/ageitgey/face_recognition) software.