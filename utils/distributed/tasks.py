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
from lib.cuckoo.core.database import Database
from lib.cuckoo.common.utils import store_temp_file


# Local Cuckoo config and database
config = Config(os.path.join(CUCKOO_ROOT, "conf", "cuckoo.conf"))
db = Database()

# Our Cuckoo-Celery App
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

    temp_file_path = store_temp_file(data, filename)
    task_id = db.add_path(file_path=temp_file_path)

    return (submit_sample.request.hostname, task_id)


@celery.task
def submit_url(url):
    """
    Submit a URL to a distributed Cuckoo worker.
    """
    print "Received a URL: %s" % url
