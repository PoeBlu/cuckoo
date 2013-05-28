"""
Setup a Celery application
    - Read config settings from cuckoo.conf
    - Create and save a celery instance for importing elsewhere

Individual tasks for use in Celery.
"""
import os
import random
from celery import Celery

from lib.cuckoo.common.config import Config
from lib.cuckoo.common.constants import CUCKOO_ROOT


config = Config(os.path.join(CUCKOO_ROOT, "conf", "cuckoo.conf"))

celery = Celery('cuckoo',
                broker=config.celery.broker,
                backend=config.celery.backend,
                include=['utils.distributed.tasks'])


@celery.task
def submit_sample(filename, data):
    """
    Submit a sample (ie, a file) to a distributed Cuckoo worker.
    """
    print "My hostname: %s" % submit_sample.request.hostname
    print "Received a file: %s" % filename
    print "File size: %s" % len(data)
    return submit_sample.request.hostname + ':' + str(random.randint(0, 1000))


@celery.task
def submit_url(url):
    """
    Submit a URL to a distributed Cuckoo worker.
    """
    print "Received a URL: %s" % url
