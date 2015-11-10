import json
import sys
from collections import OrderedDict

def sanitize_to_json():
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

    #events_dict = dict(events=events)
    #with open('trove.json', 'w') as outfile:
    #    json.dump(events_dict, outfile, indent=4, sort_keys=True)

    with open('trove_events.json', 'w') as outfile:
        for i, event in enumerate(events):

            indexing = OrderedDict(
                index = OrderedDict(_index="events", _type="event", _id=i)
            )

            json.dump(indexing, outfile)
            outfile.write('\n')
            _event = {
                "event_type": event.get("event_type", "NULL"),
                "display_name": event.get("payload").get("display_name", "NULL"),
                "instance_name": event.get("payload").get("instance_name", "NULL"),
                "instance_id": event.get("payload").get("instance_id", "NULL"),
                "launched_at": event.get("payload").get("launched_at", "NULL"),
                "region": event.get("payload").get("region", "NULL"),
                "state": event.get("payload").get("state", "NULL"),
                "tenant_id": event.get("payload").get("tenant_id", "NULL"),
                "user_id": event.get("payload").get("user_id", "NULL"),
                "priority": event.get("priority", "NULL"),
                "timestamp": event.get("timestamp", "NULL").replace(" ", "T")
            }
            json.dump(_event, outfile)
            outfile.write('\n')


if __name__ == "__main__":
    sanitize_to_json()
