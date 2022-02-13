import asyncio
import datetime
import json
import pathlib


import os

import redis
from rq import Worker, Queue, Connection, SimpleWorker

from viyyoor import models

import logging

logger = logging.getLogger(__name__)

listen = ["default"]

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

conn = redis.from_url(redis_url)


class ViyyoorWorker(SimpleWorker):
    def __init__(self, *args, **kwargs):
        settings = kwargs.pop("settings")
        super().__init__(*args, **kwargs)

        models.init_mongoengine(settings)


class WorkerServer:
    def __init__(self, settings):
        self.settings = settings

    def run(self):
        with Connection(conn):
            worker = ViyyoorWorker(list(map(Queue, listen)), settings=self.settings)
            worker.work()
