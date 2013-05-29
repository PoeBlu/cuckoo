"""
Setup a Celery application
    - Read config settings from cuckoo.conf
    - Create and save a celery instance for importing elsewhere

Individual tasks for use in Celery.
"""
import os
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


@celery.task
def list_tasks(limit=None, details=False):
    """
    Fetch all tasks and their states.
    """
    rows = db.list_tasks(limit=limit, details=details)
    tasks = []
    for row in rows:
        task = {
            "queue_id": list_tasks.request.hostname,
            "id": row.id,
            "target": row.target,
            "category": row.category,
            "status": row.status,
            "added_on": row.added_on,
            "processed": False
        }

        if os.path.exists(os.path.join(CUCKOO_ROOT, "storage", "analyses", str(task["id"]), "reports", "report.html")):
            task["processed"] = True

        if row.category == "file":
            sample = db.view_sample(row.sample_id)
            task["md5"] = sample.md5

        tasks.append(task)

    return tasks


@celery.task
def view_task(task_id, details=False):
    """
    Fetch details for a single task.
    """
    task = db.view_task(task_id, details=details)
    return task


@celery.task
def get_report(task_id, report_format="json"):
    """
    """
    formats = {
        "json": "report.json",
        "html": "report.html",
        "maec": "report.maec-1.1.xml",
        "metadata": "report.metadata.xml",
        "pickle": "report.pickle"
    }

    if report_format.lower() in formats:
        report_path = os.path.join(CUCKOO_ROOT,
                                   "storage",
                                   "analyses",
                                   task_id,
                                   "reports",
                                   formats[report_format.lower()])

    try:
        with open(report_path, "rb") as f:
            return f.read()
    except:
        raise
