import pika
import json
import sys

from es_index import index_events, index_instances
from configs import *


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
    credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(RABBITMQ_SERVER, RABBITMQ_PORT, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange=RABBITMQ_EXCHANGE, type=RABBITMQ_TYPE)

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    binding_keys = sys.argv[1:]
    if not binding_keys:
        binding_keys = [RABBITMQ_DEFAULT_BINDING_KEY]

    for binding_key in binding_keys:
        channel.queue_bind(exchange='trove', queue=queue_name, routing_key=binding_key)

    print ' [*] Waiting for notifications. To exit press CTRL+C'

    channel.basic_consume(callback, queue=queue_name, no_ack=True)
    channel.start_consuming()


def sample_data():
    with open('trove.events', 'r') as infile:
        events = []
        for line in infile.readlines():
            new_data = line.replace('\\', '')
            data = new_data.replace('null', '\"NULL\"')
            new_data = data.split('", "oslo.version":')[0]

            try:
                new_data_json = json.loads(new_data)
            except:
                sys.exit("Failed sanitizing data to json")
            events.append(new_data_json)

    # events_dict = dict(events=events)
    # with open('trove_events.json', 'w') as outfile:
    #    json.dump(events_dict, outfile, indent=4, sort_keys=True)

    print events
    #index_events(events)
    #index_instances(events)
