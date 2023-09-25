Instructions:

Essentially, all you need is ```docker-compose up -d --build```
This will create:
1) API at port 8000
2) Answering service at port 8001
3) Conversation history service at port 8002
4) Elasticsearch for answer querying at port 9200
5) RabbitMQ for queueing the messages at port 5672
6) Redis to store the messages at port 6379

Check out each service/docs for the Swagger UI docs
Ideally, this implementation should be deployed to AWS with minimal changes

To be added:
- Flower to monitor distributed Celery tasks
- Monitoring/logging collection: I'll probably deploy a Prometheus/Fluentd/Grafana stack 