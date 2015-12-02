from rabbitmq_streamer import rabbitmq_conf
from elasticsearch_dsl.connections import connections
from configs import ES_SERVER


def app():
    print "Running notifications app..."

    # Define a default Elasticsearch client
    connections.create_connection(hosts=[ES_SERVER])

    # App logic runs here
    rabbitmq_conf()

    # Display cluster health
    print(connections.get_connection().cluster.health())
