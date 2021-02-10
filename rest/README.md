# REST API and interface

A deployment that creates an external endpoint using a load balancer or ingress node. This deployment acts as an external endpoint in the cluster.

`rest-server.py` implements a Flask server that responds to the routes mentioned below. `rest-client.py` is used to send images to the `rest-server.py`.

The REST service takes in named images or URL's for images and sends those to the worker nodes for processing. Because it may take some time to process an image, the REST service returns a hash that can be used for further queries to see if the image contains faces and the names or URL's of matching images. I have assumed that URL's are unique and that once one has been processed, I don't need to process it again. I can't make the same assumption for filenames though. 

The REST routes are:

+ /scan/image/[filename] [POST] - scan the picture passed as the content of the request and with the specified filename. Compute [a hash of the contents](https://docs.python.org/3/library/hashlib.html) and send the hash and image to a worker using the `toWorker` rabbitmq exchange. The worker will add the filename to the Redis database. The response of this API will be a JSON document containing a single field `hash` that is the hash used to identify the provided image for subsequent `match` queries. For example:
```
  { 'hash' : "abcedef...128" }
```

+ /scan/url [POST] - the request body will contain a json message with a URL specifying an image. The format of the json object will be `{ "url" : "http://whatever.jpg"}`. The REST server [will retrieve the image](https://www.tutorialspoint.com/downloading-files-from-web-using-python) and proceed as for `/scan/image` but use the URL as the file name. I assumed that URL's are unique, so if we've already processed it once, we don't need to do it again.

+ /match/[hash] [GET] -- using the hash, returns a list of the image name or URL's that contain matching faces. If the hash doesn't match or there are no faces in the image, an empty list is returned.

The server is robust to failure of RabbitMQ connections. 

### There are two RabbitMQ exchanges :
+ A `topic` exchange called `logs` used for debugging and logging output
+ A `direct` exchange called `toWorker` used by the REST API to send images to the worker

I have used the topic exchange for debug messages with the topics `[hostname].rest.debug` and `[hostname].rest.info`, substituting with proper hostname. 

It is useful to create a `logs` container and deployment that listen to the logs and dumps them out to `stderr` so we can examine them using `kubectl logs..`.

