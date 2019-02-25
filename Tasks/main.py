#from __future__ import absolute_import, unicode_literals
from celery import Celery
import logging


'''
app = Celery('celeryApp',
             broker='amqp://',
             backend='amqp://',
             include=['celeryApp.tasks'])
'''
# Create the app and set the broker location (RabbitMQ)
app = Celery('celeryApp',
             backend='rpc://',
             broker='pyamqp://guest@localhost//',
             result_backend='cache+memcached://127.0.0.1:11211/')

app.conf.beat_schedule = {
    'add-every-60-seconds': {
        'task': 'celeryApp.test',
        'schedule': 60.0
    },
}
app.conf.timezone = 'UTC'


# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

cpt = 0

@app.task
def test():
    global cpt
    cpt = cpt + 1
    logging.info('TEST !!!')
    return [ 0, cpt]


if __name__ == '__main__':
    app.start()