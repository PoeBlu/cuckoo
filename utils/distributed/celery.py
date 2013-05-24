"""
Setup a Celery application
    - Read config settings from cuckoo.conf
    - Create and save a celery instance for importing elsewhere
"""
from __future__ import absolute_import
from celery import Celery
import os

from lib.cuckoo.common.config import Config
from lib.cuckoo.common.constants import CUCKOO_ROOT


config = Config(os.path.join(CUCKOO_ROOT, "conf", "cuckoo.conf"))

celery = Celery('cuckoo',
                broker=config.celery.broker,
                backend=config.celery.backend,
                include=['utils.distributed.tasks'])
