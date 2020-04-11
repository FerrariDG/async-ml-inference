from typing import (
    Any,
    Dict,
    Optional
)
from os import getenv

from celery import Celery, states
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED
)

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

api = FastAPI()
worker = Celery(broker=BROKER, backend=BACKEND)

TASKS = {
    'length': 'worker.audio_length'
}


class UrlItem(BaseModel):
    audio_url: str
    callback: bool = False


class TaskResult(BaseModel):
    id: str
    status: str
    error: Optional[str] = None
    result: Optional[Dict[Any, Any]] = None


def send_result(task_id):
    while True:
        result = worker.AsyncResult(task_id)
        if result.state in states.READY_STATES:
            break

    output = TaskResult(
        id=task_id,
        status=result.state,
        error=str(result.info) if result.failed() else None,
        result=result.get() if result.state == states.SUCCESS else None
    )

    print(output)  # Send result to somewhere


@api.post("/audio/length", status_code=HTTP_201_CREATED)
def create_task(data: UrlItem, queue: BackgroundTasks):
    task = worker.send_task(
        name=TASKS['length'],
        kwargs={'audio_url': data.audio_url}
    )
    if data.callback:
        queue.add_task(send_result, task.id)
    return {"id": task.id}


@api.get("/task/{task_id}")
def get_task_result(task_id: str):

    result = worker.AsyncResult(task_id)

    output = TaskResult(
        id=task_id,
        status=result.state,
        error=str(result.info) if result.failed() else None,
        result=result.get() if result.state == states.SUCCESS else None
    )

    return JSONResponse(
        status_code=HTTP_200_OK,
        content=output.dict()
    )
