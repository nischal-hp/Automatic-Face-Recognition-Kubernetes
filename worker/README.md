# facerec Worker

## Worker image
The worker will use the [face recognition software](https://github.com/ageitgey/face_recognition) software. This is an open-source face recognition library based on `dlib`. 

## Program to process images

There are two RabbitMQ exchanges :
+ A `topic` exchange called `logs` used for debugging and logging output
+ A `direct` exchange called `toWorker` used by the REST API to send images to the worker

Either can create a Python datatype including the image, then [`pickle` the image](https://stackoverflow.com/questions/30469575/how-to-pickle-and-unpickle-to-portable-string-in-python-3) and send it via RabbitMQ. Or, can store the image in Google object storage and send a smaller message.

Images sent by the REST front-end have an associated hash value that is used to identify the image and a name (either file name or URL). For each image (hash) I have used a Redis database that maps the hash to a set of hashes that have matching faces. Redis is a Key-Value store. Redis supports a [number of datatypes including lists and sets](https://redis.io/topics/data-types).  In many cases, the set data type will be the most appropriate because we only want a single instance of a data item associated with a key (*.e.g*, the hashes of all images that match faces in this image).

The worker should extract the list of faces in the image using `face_recognition.face_encodings`. Then, for each face in that list, we should add the face and corresponding image to the Redis database and then *compare those faces to all other faces in each image the database*. For each image containing any matching face, we would add the images (hashes) of each image to the other such that eventually we can determine the set of images that contain matching faces. Once this process is completed, we acknowledge the message.

Because Redis is a simple key-value store, we need to construct the following databases:
1. $ name \rightarrow imghash $ - Hash from image name
1. $ imghash \rightarrow \{  name \} $ - Set of origin name or url of image
1. $ imghash \rightarrow [ facrec ] $ - List or set of face recognition data for an image
1. $ imghash \rightarrow \{ imghash \} $ - Set of images containing matching faces

If an image hash has already been added, it doesn't need to be scanned again, but we should add the name to the set of origin names/urls for that image.

I have used 4 Redis databases. Redis uses numbers for database names. The '0' database is the default. I have declared the different databases using something like the following :
```
redisNameToHash = redis.Redis(host=redisHost, db=1)    # Key -> Value
redisHashToName = redis.Redis(host=redisHost, db=2)    # Key -> Set
redisHashToFaceRec = redis.Redis(host=redisHost, db=3) # Key -> Set
redisHashToHashSet = redis.Redis(host=redisHost, db=4) # Key -> Set
```

Once the database has been updated or determine nothing needs to be done we should then `acknowledge` the RabbitMQ message. We should only acknowledge it after we've processed it.

## Recognizing Faces
The face recognition library also contains [a sample implementation of a web-service to compare images to a pre-analyzed picture of Barak Obama](https://github.com/ageitgey/face_recognition/blob/master/examples/web_service_example.py) that shows how to compare matching faces.

The important code is excerpted below:
```
    # Load the uploaded image file
    img = face_recognition.load_image_file(file_stream)
    # Get face encodings for any faces in the uploaded image
    unknown_face_encodings = face_recognition.face_encodings(img)
    ...
    if len(unknown_face_encodings) > 0:
        face_found = True
        # See if the first face in the uploaded image matches the known face of Obama
        match_results = face_recognition.compare_faces([known_face_encoding], unknown_face_encodings[0])
        if match_results[0]:
            is_obama = True
```
This uses [the `face_recognition.face_encodings` function](https://face-recognition.readthedocs.io/en/latest/face_recognition.html) to retrieve a vector/list of characteristics concerning the image.

## Debugging

At each step of the processing, we should log debug information using the `topic` queue and `[hostname].worker.debug`. When we've added the data to the database, we must log that as `[hostname].worker.info`, substituting the proper worker name.


## Development Steps Followed

Rather than immediately pushing everything to the Kubernetes cluster, we should first deploy Redis and Rabbitmq and then use the `kubectl port-forward` mechanism to expose those services on the local machine. The script `deploy-local-dev.sh` is for that purpose.

Can then work on the server by running e.g. `docker run --rm -it -v $(pwd)/src:/app facerec /bin/bash` and then trying the code in `/app` in the container rather than building and installing the face recognition software locally.

The hostname for Redis and RabbitMQ can be got from environment variables that we can either set in the shell or override in the `worker-deployment.yaml`. 

Have used the `log_info` and `log_debug` routines that write to the `logs` topic to simplify the development. 


## Database consistency

Although Redis is basically a key-value store, it [still supports transactions within a particular database](https://fabioconcina.github.io/blog/transactions-in-redis-with-python/). This is used to prevent inconsistencies within the database (i.e. the worker may abort after entering some information but before entering other from processing the face recognition). This can also be problematic if the REST front-end uses the database to avoid re-fetch URL's that it has already loaded -- we may have entered the URL name in `redisNameToHash` but not yet processed the image completely.