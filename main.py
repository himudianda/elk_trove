import pika
import json
import sys
import datetime
from elasticsearch_dsl import DocType, String, Date, Integer
from elasticsearch_dsl.connections import connections
from elasticsearch.exceptions import NotFoundError


# Define a default Elasticsearch client
connections.create_connection(hosts=['localhost'])


class TroveEvent(DocType):
    event_type = String(index='not_analyzed')
    display_name = String(index='not_analyzed')
    instance_name = String(index='not_analyzed')
    instance_id = String(index='not_analyzed')
    region = String(index='not_analyzed')
    state = String(index='not_analyzed')
    tenant_id = String(index='not_analyzed')
    user_id = String(index='not_analyzed')
    priority = String(index='not_analyzed')
    timestamp = Date()

    class Meta:
        index = 'trove_events'


class TroveInstance(DocType):
    request_id = String(index='not_analyzed')
    request_type = String(index='not_analyzed')
    creation_start_time = Date()
    creation_end_time = Date()
    create_time_taken_secs = Integer()
    deletion_start_time = Date()
    deletion_end_time = Date()
    delete_time_taken_secs = Integer()

    class Meta:
        index = 'trove_instances'


def sanitize():
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

    return events


def index_events(events):
    # create the mappings in elasticsearch
    TroveEvent.init()

    for event in events:
        _event = {
            "event_type": event.get("event_type", "NULL"),
            "display_name": event.get("payload").get("display_name", "NULL"),
            "instance_name": event.get("payload").get("instance_name", "NULL"),
            "instance_id": event.get("payload").get("instance_id", "NULL"),
            "region": event.get("payload").get("region", "NULL"),
            "state": event.get("payload").get("state", "NULL"),
            "tenant_id": event.get("payload").get("tenant_id", "NULL"),
            "user_id": event.get("payload").get("user_id", "NULL"),
            "priority": event.get("priority", "NULL"),
            "timestamp": event.get("timestamp", None).replace(" ", "T")
        }

        trove_event = TroveEvent(**_event)
        trove_event.save()

    # Display cluster health
    print(connections.get_connection().cluster.health())


def index_instances(events):
    TroveInstance.init()

    tracked_events = [
        'dbaas.instance_create.start',
        'dbaas.instance_create.end',
        'dbaas.instance_delete.start',
        'dbaas.instance_delete.end'
    ]

    for event in events:
        event_type = event.get("event_type", None)
        if not event_type or event_type not in tracked_events:
            continue
        request_id = event.get("payload").get("request_id", None)
        if not request_id:
            continue

        try:
            trove_instance = TroveInstance.get(id=request_id)
        except NotFoundError:
            _instance = {
                "meta": {'id': request_id},
                "request_id": request_id
            }
            if event_type == "dbaas.instance_create.start":
                _instance['creation_start_time'] = event.get("timestamp", None).replace(" ", "T")
                _instance['request_type'] = "DB Create"
            if event_type == "dbaas.instance_delete.start":
                _instance['deletion_start_time'] = event.get("timestamp", None).replace(" ", "T")
                _instance['request_type'] = "DB Delete"

            trove_instance = TroveInstance(**_instance)
        else:
            if event_type == "dbaas.instance_create.end":
                creation_end_time = event.get("timestamp", None).replace(" ", "T")
                trove_instance.creation_end_time = creation_end_time

                start_time = trove_instance.creation_start_time
                end_time = datetime.datetime.strptime(creation_end_time, "%Y-%m-%dT%H:%M:%S.%f")

                delta = end_time - start_time
                (_min, _sec) = divmod(delta.days * 86400 + delta.seconds, 60)
                trove_instance.create_time_taken_secs = _min*60 + _sec

            elif event_type == "dbaas.instance_delete.end":
                deletion_end_time = event.get("timestamp", None).replace(" ", "T")
                trove_instance.deletion_end_time = deletion_end_time

                start_time = trove_instance.deletion_start_time
                end_time = datetime.datetime.strptime(deletion_end_time, "%Y-%m-%dT%H:%M:%S.%f")

                delta = end_time - start_time
                (_min, _sec) = divmod(delta.days * 86400 + delta.seconds, 60)
                trove_instance.delete_time_taken_secs = _min*60 + _sec

        trove_instance.save()
    # Display cluster health
    print(connections.get_connection().cluster.health())


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


def main():
    rabbitmq_conf()

    #events = sanitize()
    #index_events(events)
    #ndex_instances(events)


if __name__ == "__main__":
    main()
