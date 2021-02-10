# Redis database

A single-pod deployment that provides a Redis database and a service called `redis` so that worker nodes can use DNS names to locate the instance. The provided deployment uses [the image provided by the Redis developers](https://hub.docker.com/_/redis).

If redis pod is deleted, the database will also be deleted because no volume is provided for the data. To avoid that problem, we can create [a kubernetes Persistent Volume and Persistent Volume claim](https://cloud.google.com/kubernetes-engine/docs/concepts/persistent-volumes).
