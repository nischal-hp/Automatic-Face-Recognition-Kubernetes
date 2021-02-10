#
# Worker server
#
import pickle
import platform
from PIL import Image
import io
import os
import sys
import pika
import redis
import hashlib
import face_recognition

hostname = platform.node()

##
## Configure test vs. production
##
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

#print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost,redisHost))

# Define the RabbitMQ connection
connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitMQHost))
channel = connection.channel()
# Four Redis databases as described
redisNameToHash = redis.Redis(host=redisHost, db=1)    # Key -> Value
redisHashToName = redis.Redis(host=redisHost, db=2)    # Key -> Set
redisHashToFaceRec = redis.Redis(host=redisHost, db=3) # Key -> Set
redisHashToHashSet = redis.Redis(host=redisHost, db=4) # Key -> Set

def callback(ch, method, properties, body):
    # Get the filename, hash of the image filename and the actual image
    filename,hashedMessage,image = properties.headers['filename'],properties.headers['md5'],pickle.loads(properties.headers['image'])
    unknown_face_encodings=[]
    match_results=[]
    # io library is used to simulate image being on a file system
    image=io.BytesIO(image)
    # Get the face encodings for the current image
    unknown_face_encodings = face_recognition.face_encodings(face_recognition.load_image_file(image))
    # Add each face in the image to the 3rd Redis database
    for eachFace in unknown_face_encodings:
        redisHashToFaceRec.sadd(hashedMessage,pickle.dumps(eachFace))
    # If no. of faces detected are more than 0
    if len(unknown_face_encodings) > 0:
        # Iterate through all the keys in the database
        for previous_keys in redisHashToFaceRec.keys(pattern='*'):
            # Get all the values for the particular key
            all_faces=pickle.loads(redisHashToFaceRec.smembers(previous_keys))
            # See if the first face in the uploaded image matches an already known face
            match_results = face_recognition.compare_faces(list(all_faces), unknown_face_encodings[0])
            for each_result in match_results:
                # If a match has been found, add it to the database
                if each_result==True:
                    redisHashToHashSet.sadd(previous_keys,hashedMessage)  
    # Do an acknowledgement                
    channel.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='toWorker', on_message_callback=callback)
channel.start_consuming()