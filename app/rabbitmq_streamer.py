import pika
import json
import sys

from es_index import index_events, index_instances


def callback(ch, method, properties, body):

    # Sanitize the data
    new_data = body.replace('\\', '')
    data = new_data.replace('null', '\"NULL\"')
    new_data = data.split('", "oslo.version":')[0]
    new_data = new_data.split('{"oslo.message": "')[1]

    try:
        new_data_json = json.loads(new_data)
    except:
        sys.exit("Failed sanitizing data to json")

    events = []
    print new_data_json
    events.append(new_data_json)
    index_events(events)
    index_instances(events)


def rabbitmq_conf():
    credentials = pika.PlainCredentials('rabbitmq', 'rabbitmq')
    parameters = pika.ConnectionParameters('rtp10-svc-4-medium01-troverabbitmq-001', 5672, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange='trove', type='topic')

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    binding_keys = sys.argv[1:]
    if not binding_keys:
        print >> sys.stderr, "Usage: %s [binding_key]..." % (sys.argv[0],)
        sys.exit(1)

    for binding_key in binding_keys:
        channel.queue_bind(exchange='trove', queue=queue_name, routing_key=binding_key)

    print ' [*] Waiting for notifications. To exit press CTRL+C'

    channel.basic_consume(callback, queue=queue_name, no_ack=True)
    channel.start_consuming()
