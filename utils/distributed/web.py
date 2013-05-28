#!/usr/bin/env python

import os
import sys
import logging
import argparse
try:
    from jinja2.loaders import FileSystemLoader
    from jinja2.environment import Environment
except ImportError:
    sys.stderr.write("ERROR: Jinja2 library is missing")
    sys.exit(1)
try:
    from bottle import route, run, static_file, redirect, request, HTTPError, hook, response
except ImportError:
    sys.stderr.write("ERROR: Bottle library is missing")
    sys.exit(1)

logging.basicConfig()
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", ".."))

from lib.cuckoo.common.constants import CUCKOO_ROOT

# Templating engine.
env = Environment()
env.loader = FileSystemLoader(os.path.join(CUCKOO_ROOT, "data", "html"))

from utils.distributed import tasks


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


@route("/distributed/")
def index():
    context = {}
    template = env.get_template("distributed/submit.html")
    return template.render({"context": context})


@route("/distributed/browse")
def browse():
    """
    """
    r = tasks.get_task_list.delay()
    # Blocking!
    task_list = r.get()
    template = env.get_template("distributed/browse.html")
    return template.render({"rows": task_list})


@route("/static/<filename:path>")
def server_static(filename):
    return static_file(filename, root=os.path.join(CUCKOO_ROOT, "data", "html"))


@route("/distributed/submit", method="POST")
def submit():
    context = {}
    errors = False

    package = request.forms.get("package", "")
    options = request.forms.get("options", "")
    priority = request.forms.get("priority", 1)
    timeout = request.forms.get("timeout", "")
    data = request.files.file

    try:
        priority = int(priority)
    except ValueError:
        context["error_toggle"] = True
        context["error_priority"] = "Needs to be a number"
        errors = True

    if not data:
        context["error_toggle"] = True
        context["error_file"] = "Mandatory"
        errors = True

    if errors:
        template = env.get_template("distributed/submit.html")
        return template.render({"timeout": timeout,
                                "priority": priority,
                                "options": options,
                                "package": package,
                                "context": context})

    r = tasks.submit_sample.delay(data.filename, data.file.read())
    # This is blocking!
    task_id = r.get()

    template = env.get_template("distributed/success.html")
    return template.render({"queue_id": task_id[0],
                            "task_id": task_id[1],
                            "submitfile": data.filename.decode("utf-8")})


@route("/distributed/view/<queue_id>/<task_id>")
def view(queue_id, task_id):
    if not task_id.isdigit():
        return HTTPError(code=404, output="The specified ID is invalid")

    r = tasks.get_html_report.apply_async(args=[task_id], queue=queue_id)
    return r.get()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host", help="Host to bind the web server on", default="0.0.0.0", action="store", required=False)
    parser.add_argument("-p", "--port", help="Port to bind the web server on", default=8080, action="store", required=False)
    args = parser.parse_args()

    run(host=args.host, port=args.port, reloader=True)
