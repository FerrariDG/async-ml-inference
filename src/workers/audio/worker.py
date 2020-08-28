"""Celery worker for audio Length extraction."""
from io import BytesIO
from sys import exit
from time import sleep
from typing import (
    Any,
    Dict
)
from urllib import request
import traceback

from celery import Celery, states
from celery.exceptions import Ignore
from librosa import load, get_duration

from workers.utils import backend
from workers.utils import broker

if not backend.is_backend_running():
    exit()

if not broker.is_broker_running():
    exit()

audio = Celery("audio", broker=broker.get_broker_url(), backend=backend.get_backend_url())


@audio.task(bind=True, name="audio.audio_length")
def audio_length(self, audio_url: str) -> Dict[str, Any]:
    print('Executing task id {0.id}, args: {0.args!r} kwargs: {0.kwargs!r}'.format(self.request))

    try:
        payload = request.urlopen(audio_url)
        data = payload.read()
    except Exception as e:
        self.update_state(
            state=states.FAILURE,
            meta={
                'exc_type': type(e).__name__,
                'exc_message': str(e),  # info
                'traceback': traceback.format_exc().split('\n')
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
