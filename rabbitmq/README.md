# RabbitMQ Messaging

A single-pod deployment that provides a RabbitMQ message server and a service called `rabbitmq` so that worker nodes can use DNS names to locate the instance. The provided deployment uses [the one provided by the Rabbitmq developers](https://hub.docker.com/_/rabbitmq).

Here, I have not created any queues or exchanges; as this will be done by the worker node.

