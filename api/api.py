from os import getenv

from celery import Celery, states
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_500_INTERNAL_SERVER_ERROR
)

REDIS_HOST = getenv("REDIS_HOST", "localhost")
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

api = FastAPI()
worker = Celery(broker=BROKER, backend=BACKEND)

TASKS = {
    'length': 'worker.audio_length'
}


class UrlItem(BaseModel):
    url: str


@api.post("/audio/length", status_code=HTTP_201_CREATED)
def create_task(data: UrlItem):
    task = worker.send_task(TASKS['length'], kwargs={'url': data.url})
    return {"task_id": task.id}


@api.get("/task/{task_id}")
def get_task_result(task_id: str):
    result = worker.AsyncResult(task_id)

    if result.state not in states.READY_STATES:
        return JSONResponse(
            status_code=HTTP_202_ACCEPTED,
            content={
                "task_id": task_id,
                "status": result.state
            }
        )

    if result.failed():
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "task_id": task_id,
                "status": states.FAILURE,
                "error": str(result.info)
            }
        )

    return {"task_id": task_id, "status": states.SUCCESS, "result": result.get()}
