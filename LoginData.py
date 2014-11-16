import sys
import os

__author__ = 'daan'

# this just pulls the login data from the corresponding environment variables
# usernames and the default dockered twister login data are
# not considered sensitive enough to protect, so see below for their defaults :)

twister_host = os.getenv("TWISTER_PORT_28332_TCP_ADDR", "127.0.0.1")
twister_port = os.getenv("TWISTER_PORT_28332_TCP_PORT", "28332")
TWISTER_RPC_URL = "http://user:pwd@%s:%s" % (twister_host, twister_port)

RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'twisterTaskPublisher')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
if not RABBITMQ_PASSWORD:
    print("could not find RabbitMQ password in environment!")
    sys.exit(1)
RABBITMQ_PUBLISHER_URL = 'amqp://%s:%s@localhost//' % (RABBITMQ_USER, RABBITMQ_PASSWORD)
