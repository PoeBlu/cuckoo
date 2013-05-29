#!/usr/bin/env python

import os
import sys
import json
import argparse
import logging

try:
    from bottle import Bottle, route, run, request, server_names, ServerAdapter, hook, response, HTTPError
except ImportError:
    sys.exit("ERROR: Bottle.py library is missing")


logging.basicConfig()
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", ".."))

from lib.cuckoo.common.constants import CUCKOO_ROOT
from lib.cuckoo.common.config import Config

# Local Cuckoo config and database
config = Config(os.path.join(CUCKOO_ROOT, "conf", "cuckoo.conf"))

from utils.distributed import tasks


def jsonize(data):
    """Converts data dict to JSON.
    @param data: data dict
    @return: JSON formatted data
    """ 
    response.content_type = "application/json; charset=UTF-8"
    return json.dumps(data, sort_keys=False, indent=4)

@hook("after_request")
def custom_headers():
    """Set some custom headers across all HTTP responses."""
    response.headers["Server"] = "Machete Server"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Pragma"] = "no-cache"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Expires"] = "0"

@route("/tasks/create/file", method="POST")
def tasks_create_file():
    response = {}

    data = request.files.file
    package = request.forms.get("package", "")
    timeout = request.forms.get("timeout", "")
    priority = request.forms.get("priority", 1)
    options = request.forms.get("options", "")
    machine = request.forms.get("machine", "")
    platform = request.forms.get("platform", "")
    custom = request.forms.get("custom", "")
    memory = request.forms.get("memory", False)
    if memory:
        memory = True
    enforce_timeout = request.forms.get("enforce_timeout", False)
    if enforce_timeout:
        enforce_timeout = True

    r = tasks.submit_sample.delay(data.filename, data.file.read())
    # This is blocking!
    task_id = r.get()


    response["task_id"] = task_id
    return jsonize(response)

@route("/tasks/create/url", method="POST")
def tasks_create_url():
    response = {}

    url = request.forms.get("url")
    package = request.forms.get("package", "")
    timeout = request.forms.get("timeout", "")
    priority = request.forms.get("priority", 1)
    options = request.forms.get("options", "")
    machine = request.forms.get("machine", "")
    platform = request.forms.get("platform", "")
    custom = request.forms.get("custom", "")
    memory = request.forms.get("memory", False)
    if memory:
        memory = True
    enforce_timeout = request.forms.get("enforce_timeout", False)
    if enforce_timeout:
        enforce_timeout = True

    r = tasks.submit_url.delay(url)
    task_id = r.get()

    response["task_id"] = task_id
    return jsonize(response)

@route("/tasks/list", method="GET")
@route("/tasks/list/<limit>", method="GET")
def tasks_list(limit=None):
    response = {}

    response["tasks"] = []
    workers = [x.strip() for x in config.celery.workers.split()]
    task_list = []
    for worker in workers:
        r = tasks.list_tasks.apply_async(kwargs={"limit": limit, "details": True},
                                         queue=worker)
        task_list += r.get()

    for task in task_list:
        response["tasks"].append(task)

    return jsonize(response)


@route("/tasks/view/<queue_id>/<task_id>", method="GET")
def tasks_view(queue_id, task_id):
    response = {}

    r = tasks.view_task.apply_async(args=[task_id], kwargs={'details': True},
                                    queue=queue_id)
    task = r.get()
    if task:
        entry = task.to_dict()
        entry["guest"] = {}
        if task.guest:
            entry["guest"] = task.guest.to_dict()

        entry["errors"] = []
        for error in task.errors:
            entry["errors"].append(error.message)

        response["task"] = entry
    else:
        return HTTPError(404, "Task not found")

    return jsonize(response)


@route("/tasks/report/<queue_id>/<task_id>", method="GET")
@route("/tasks/report/<queue_id>/<task_id>/<report_format>", method="GET")
def tasks_report(queue_id, task_id, report_format="json"):
    response = {}

    formats = {
        "json": "report.json",
        "html": "report.html",
        "maec": "report.maec-1.1.xml",
        "metadata": "report.metadata.xml",
        "pickle": "report.pickle"
    }

    if not report_format.lower() in formats:
        return HTTPError(400, "Invalid report format")

    r = tasks.get_report.apply_async(args=[task_id],
                                     kwargs={"report_format": report_format},
                                     queue=queue_id)

    return r.get()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host", help="Host to bind the API server on", default="localhost", action="store", required=False)
    parser.add_argument("-p", "--port", help="Port to bind the API server on", default=8090, action="store", required=False)
    args = parser.parse_args()

    run(host=args.host, port=args.port)
