from elasticsearch_dsl.connections import connections
from configs import ES_SERVER
import sys
import json
from configs import *

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

    write_logs(events)

def write_logs(events):
	'''
    with open('trove_events.json', 'w') as outfile:
        for event in events:
            json.dump(event, outfile, indent=4, sort_keys=True)
    '''
	with open('trove_events.log', 'w') as outfile:
		for event in events:
			if not 'payload' in event:
				continue
			if not 'instance_id' in event['payload']:
				continue
			if not 'user_id' in event['payload']:
				continue
			if not 'display_name' in event['payload']:
				continue
			print "Writing .."
			out_format = "{user_id} {tenant_id}"
			outfile.write(out_format.format(
					user_id = event['payload']['user_id'],
					tenant_id = event['payload']['tenant_id'],
				)
			)
			outfile.write('\n')

def main():
    connections.create_connection(hosts=[ES_SERVER])
    sample_data()

    # Display cluster health
    #print(connections.get_connection().cluster.health())


if __name__ == "__main__":
	main()