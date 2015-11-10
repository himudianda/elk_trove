import json
import sys
from elasticsearch_dsl import DocType, String, Date
from elasticsearch_dsl.connections import connections


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
            "timestamp": event.get("timestamp", "NULL").replace(" ", "T")
        }

        trove_event = TroveEvent(**_event)
        trove_event.save()

    # Display cluster health
    print(connections.get_connection().cluster.health())


def main():
    events = sanitize()
    index_events(events)


if __name__ == "__main__":
    main()
