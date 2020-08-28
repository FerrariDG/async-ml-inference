from datetime import date, timedelta
from os import getenv
from random import random
from typing import (
    Any,
    Dict,
    Tuple
)

from joblib import Parallel, delayed
from requests import post, get
from retrying import retry

AUDIO_URLS = tuple(
    f"http://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_00{id:02}_8k.wav"
    for id in range(10, 65)
)

API_URL = getenv("API_URL", "http://0.0.0.0:5000")

ENDPOINT_LENGTH = API_URL + "/audio/length"

ENDPOINT_RESULT = API_URL + "/euro/results"

ENDPOINT_TASK_RESULT = API_URL + "/task/{}"

STATUS_CREATED = 201
STATUS_PENDING = 202


def make_date_post(dt: date) -> Tuple[int, str]:
    callback = random() < 0.5
    response = post(ENDPOINT_RESULT, json={'draw_date': dt.strftime("%d-%m-%Y"), 'callback': callback})
    task_id = response.json()['id'] if response.status_code == STATUS_CREATED else None
    return (response.status_code, task_id)


def make_post(url: str) -> Tuple[int, str]:
    callback = random() < 0.5
    response = post(ENDPOINT_LENGTH, json={'audio_url': url, 'callback': callback})
    task_id = response.json()['id'] if response.status_code == STATUS_CREATED else None
    return (response.status_code, task_id)


@retry(stop_max_attempt_number=10, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def get_result(task_id: str) -> Dict[Any, Any]:
    response = get(ENDPOINT_TASK_RESULT.format(task_id))
    if response.status_code == STATUS_PENDING:
        raise Exception("Task on progress")

    return response.json()


if __name__ == "__main__":

    print("Sending audio urls")
    audio_tasks = Parallel(n_jobs=2, prefer="threads")(
        delayed(make_post)(url)
        for url in AUDIO_URLS
    )

    print("Sending dates")
    euro_tasks = Parallel(n_jobs=2, prefer="threads")(
        delayed(make_date_post)(date.fromordinal(dt))
        for dt in range((date.today() - timedelta(days=15)).toordinal(), date.today().toordinal())
    )

    tasks = euro_tasks + audio_tasks

    print("Geting results")
    results = Parallel(n_jobs=2, prefer="threads")(
        delayed(get_result)(task_id)
        for (status, task_id) in tasks if status == STATUS_CREATED
    )

    for idx, data in enumerate(results):
        output = data['result'] if data['status'] == 'SUCCESS' else data['error']
        print(f"{idx+1:2d} - {data['id']} - {data['status']} - {output}")
