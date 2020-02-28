from io import BytesIO
from os import getenv
from urllib import request

from celery import Celery, states
from celery.exceptions import Ignore
from librosa import load, get_duration

REDIS_HOST = getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = getenv("REDIS_PORT", "6379")
REDIS_USER = getenv("REDIS_USER", "")
REDIS_PASS = getenv("REDIS_PASS", "")

REDIS_DB_BROKER = getenv("REDIS_DB_BROKER", "0")
REDIS_DB_BACKEND = getenv("REDIS_DB_BACKEND", "1")

BROKER = "redis://{userpass}{hostname}{port}{db}".format(
    hostname=REDIS_HOST,
    userpass=REDIS_USER + ":" + REDIS_PASS + "@" if REDIS_USER else "",
    port=":" + REDIS_PORT if REDIS_PORT else "",
    db="/" + REDIS_DB_BROKER if REDIS_DB_BROKER else ""
)

BACKEND = "redis://{userpass}{hostname}{port}{db}".format(
    hostname=REDIS_HOST,
    userpass=REDIS_USER + ":" + REDIS_PASS + "@" if REDIS_USER else "",
    port=":" + REDIS_PORT if REDIS_PORT else "",
    db="/" + REDIS_DB_BACKEND if REDIS_DB_BACKEND else ""
)

worker = Celery("audio", broker=BROKER, backend=BACKEND)


@worker.task(bind=True, name="worker.audio_length")
def audio_length(self, url: str) -> int:

    try:
        payload = request.urlopen(url)
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

    return get_duration(y, sr)
