from kombu import Queue

broker_url = 'pyamqp://guest:guest@rabbitmq:5672//'
result_backend = 'redis://redis:6379/0'

# Dead Letter Queue Configurations
task_queues = {
    Queue('default', routing_key='task.#', queue_arguments={
        'x-message-ttl': 3600000,
        'x-dead-letter-exchange': 'dead_letter_exchange',
        'x-dead-letter-routing-key': 'dead_letter'
    }),
    Queue('dead_letter', routing_key='dead_letter')
}
task_default_queue = 'default'
task_default_routing_key = 'task.default'
task_default_exchange_type = 'default'
task_default_exchange_type = 'topic'
# broker_connection_retry_on_startup = True
