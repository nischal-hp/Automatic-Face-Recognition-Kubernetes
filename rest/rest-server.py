##
from flask import Flask, request, Response
import jsonpickle, pickle
import platform
import io, os, sys
import pika, redis
import hashlib, requests
import wget

##
## Configure test vs. production
##
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

#print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost,redisHost))

app = Flask(__name__)
# Four Redis databases as described
redisNameToHash = redis.Redis(host=redisHost, db=1)    # Key -> Value
redisHashToName = redis.Redis(host=redisHost, db=2)    # Key -> Set
redisHashToFaceRec = redis.Redis(host=redisHost, db=3) # Key -> Set
redisHashToHashSet = redis.Redis(host=redisHost, db=4) # Key -> Set
# Added this for health checking
@app.route('/', methods=['GET'])
def hello():
    return 'Added this, for health checking'
# When the Image filename is provided
@app.route('/scan/image/<fileName>', methods=['POST'])
def scan_image(fileName):
    # Get the hash of the filename
    hashedMessage = hashlib.md5(fileName.encode()).hexdigest()
    # If an image is being scanned for the first time
    if redisNameToHash.get(fileName)==None:
        # Add the hashed name to 2 redis databases as required
        redisNameToHash.set(fileName, hashedMessage)
        redisHashToName.sadd(hashedMessage,fileName)
        # Establish the RabbitMQ connection
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
        channel = connection.channel()
        # Below exchange is of the type 'toWorker'
        channel.exchange_declare(exchange='toWorker', exchange_type='direct', queue='toWorker')
        channel.basic_publish(exchange='toWorker',routing_key='tasks',body=request.data,properties=pika.BasicProperties(delivery_mode=2, headers = {'filename':fileName, 'md5': hashedMessage, 'image': pickle.dumps(fileName)}))       
        print(" Sent %r" % hashedMessage)
        # Below exchange is of the type 'logs'
        channel.exchange_declare(exchange='logs', exchange_type='topic')
        channel.basic_publish(exchange='logs', routing_key='logs', body=request.data)
        # Close the RabbitMQ connection
        connection.close()
        # Send back the response in the required format
        response = {'hash' : hashedMessage}
        response_pickled = jsonpickle.encode(response)
        return Response(response=response_pickled, status=200, mimetype="application/json")
    # If an image hash has already been added, just add the name to the set of origin names/urls for that image
    else:
        redisHashToName.sadd(hashedMessage,fileName)

# When the Image URL is provided
@app.route('/scan/url', methods=['POST'])
def scan_url():
    fileName = request.url
    # Image has to be first downloaded onto the local system
    data= wget.download(fileName)
    # Get the hash of the filename
    hashedMessage = hashlib.md5(fileName.encode()).hexdigest()
    # If an image is being scanned for the first time
    if redisNameToHash.get(fileName)==None:
        # Add the hashed name to 2 redis databases as required
        redisNameToHash.set(fileName, hashedMessage)
        redisHashToName.sadd(hashedMessage,fileName)
        # Establish the RabbitMQ connection
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
        channel = connection.channel()
        # Below exchange is of the type 'toWorker'
        channel.exchange_declare(exchange='toWorker', exchange_type='direct', queue='tasks')
        channel.basic_publish(exchange='toWorker',routing_key='tasks',body=request.data,properties=pika.BasicProperties(delivery_mode=2, headers = {'filename':file_names, 'md5': hashedMessage, 'image': pickle.dumps(file_names)}))
        print(" Sent %r" % hashedMessage)
        # Below exchange is of the type 'logs'
        channel.exchange_declare(exchange='logs', exchange_type='topic')
        channel.basic_publish(exchange='logs', routing_key='logs', body=request.data)
        # Close the RabbitMQ connection
        connection.close()
        response = {'hash' : hashedMessage}
        response_pickled = jsonpickle.encode(response)
        return Response(response=response_pickled, status=200, mimetype="application/json")
    # If an image hash has already been added, just add the name to the set of origin names/urls for that image
    else:
        redisHashToName.sadd(hashedMessage,fileName)

# When the Image Match has to be
@app.route('/match/<hash>', methods=['GET'])
def match_faces(hash):
    # List to store the final result
    result=[]
    # Get the values from the 3rd Redis database
    hash_faces = redisHashToHashSet.smembers(hash)
    for each_face in hash_faces:
        result.append(redisHashToName.smembers(each_face))
    # Send back the response
    return Response(response=result, status=200, mimetype="application/json")

app.run(host="0.0.0.0", port=5000)