from io import BytesIO
from os import getenv
from time import sleep
from typing import (
    Any,
    Dict
)
from urllib import request

from celery import Celery, states
from celery.exceptions import Ignore
from librosa import load, get_duration

REDIS_HOST = getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = getenv("REDIS_PORT", "6379")
REDIS_USER = getenv("REDIS_USER", "")
REDIS_PASS = getenv("REDIS_PASS", "")
REDIS_DB = getenv("REDIS_DB_BACKEND", "0")

RABBITMQ_HOST = getenv("RABBITMQ_HOST", "127.0.0.1")
RABBITMQ_PORT = getenv("RABBITMQ_PORT", "5672")
RABBITMQ_USER = getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = getenv("RABBITMQ_PASS", "guest")
RABBITMQ_VHOST = getenv("RABBITMQ_VHOST", "")

# RabbitMQ connection string: amqp://user:pass@localhost:5672/myvhost
BROKER = "amqp://{userpass}{hostname}{port}{vhost}".format(
    hostname=RABBITMQ_HOST,
    userpass=RABBITMQ_USER + ":" + RABBITMQ_PASS + "@" if RABBITMQ_USER else "",
    port=":" + RABBITMQ_PORT if RABBITMQ_PORT else "",
    vhost="/" + RABBITMQ_VHOST if RABBITMQ_VHOST else ""
)

# Redis connection string: redis://user:pass@hostname:port/db_number
BACKEND = "redis://{userpass}{hostname}{port}{db}".format(
    hostname=REDIS_HOST,
    userpass=REDIS_USER + ":" + REDIS_PASS + "@" if REDIS_USER else "",
    port=":" + REDIS_PORT if REDIS_PORT else "",
    db="/" + REDIS_DB if REDIS_DB else ""
)

worker = Celery("audio", broker=BROKER, backend=BACKEND)


@worker.task(bind=True, name="worker.audio_length")
def audio_length(self, audio_url: str) -> Dict[str, Any]:

    try:
        payload = request.urlopen(audio_url)
        data = payload.read()
    except Exception as e:
        self.update_state(
            state=states.FAILURE,
            meta={
                'exc_type': type(e).__name__,
                'exc_message': str(e),
                "message": "Unable to download file"
            }
        )
        raise Ignore()

    try:
        y, sr = load(BytesIO(data), sr=None)
    except Exception as e:
        self.update_state(
            state=states.FAILURE,
            meta={
                'exc_type': type(e).__name__,
                'exc_message': str(e),
                "message": "Unable to load file"
            }
        )
        raise Ignore()

    length = get_duration(y, sr)
    sleep(length / 10)  # Simulate a long task processing

    return {
        'audio_length': length
    }
