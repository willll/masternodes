from __future__ import absolute_import, unicode_literals
from celery import Celery

app = Celery('Tasks',
             broker='amqp://',
             backend='amqp://',
             include=['Tasks.tasks'],
             result_backend='cache+memcached://127.0.0.1:11211/')

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
