import pika
import sys

# Run this script as follows:
# ssh root@rtp10-svc-4-medium01-troverabbitmq-001
# python trove.py "monitoring.*"
# This should spit out all the spew

credentials = pika.PlainCredentials('rabbitmq', 'rabbitmq')

parameters = pika.ConnectionParameters('localhost',
                                       5672,
                                       '/',
                                       credentials)

connection = pika.BlockingConnection(parameters)

channel = connection.channel()

channel.exchange_declare(exchange='trove',
                         type='topic')

result = channel.queue_declare(exclusive=True)
queue_name = result.method.queue

binding_keys = sys.argv[1:]
if not binding_keys:
    print >> sys.stderr, "Usage: %s [binding_key]..." % (sys.argv[0],)
    sys.exit(1)

for binding_key in binding_keys:
    channel.queue_bind(exchange='trove',
                       queue=queue_name,
                       routing_key=binding_key)

print ' [*] Waiting for notifications. To exit press CTRL+C'


def callback(ch, method, properties, body):
    print " [x] %r:%r" % (method.routing_key, body,)

channel.basic_consume(callback,
                      queue=queue_name,
                      no_ack=True)

channel.start_consuming()
