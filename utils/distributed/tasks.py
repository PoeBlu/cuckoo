"""
Individual tasks for use in Celery.
"""
from utils.distributed.celery import celery


@celery.task
def submit_sample(filename, data):
    """
    Submit a sample (ie, a file) to a distributed Cuckoo worker.
    """
    print "Received a file: %s" % filename
    print "File size: %s" % len(data)


@celery.task
def submit_url(url):
    """
    Submit a URL to a distributed Cuckoo worker.
    """
    print "Received a URL: %s" % url
