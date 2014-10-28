from __future__ import absolute_import

from celery import Celery
from LoginData import RABBITMQ_PUBLISHER_URL

app = Celery('TwisterScraper',
             broker=RABBITMQ_PUBLISHER_URL,
             # backend='amqp://',
             include=['TwisterScraper.RpcScraper'])

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
    CELERY_ACCEPT_CONTENT=['json','pickle'],
)

if __name__ == '__main__':
    app.start()
