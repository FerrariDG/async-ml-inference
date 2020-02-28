from os import getenv
from multiprocessing import cpu_count

from joblib import Parallel, delayed
from requests import post, get
from retrying import retry

AUDIO_URLS = tuple(
    f"http://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_00{id:02}_8k.wav"
    for id in range(10, 65)
)

API_URL = getenv("API_URL", "http://127.0.0.1:8000")

ENDPOINT_LENGTH = API_URL + "/audio/length"

ENDPOINT_RESULT = API_URL + "/task/{}"

STATUS_CREATED = 201
STATUS_PENDING = 202


def make_post(url):
    response = post(ENDPOINT_LENGTH, json={'url': url})
    task_id = response.json()['task_id'] if response.status_code == STATUS_CREATED else None
    return (response.status_code, task_id)


@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
def get_result(task_id):
    response = get(ENDPOINT_RESULT.format(task_id))
    if response.status_code == STATUS_PENDING:
        raise Exception("Task on progress")

    return response.json()


if __name__ == "__main__":
    print("Sending audio urls")
    tasks = Parallel(n_jobs=cpu_count(), prefer="threads")(
        delayed(make_post)(url)
        for url in AUDIO_URLS
    )

    print("Geting results")
    results = Parallel(n_jobs=cpu_count(), prefer="threads")(
        delayed(get_result)(task_id)
        for (status, task_id) in tasks if status == STATUS_CREATED
    )

    for idx, data in enumerate(results):
        output = data['result'] if data['status'] == 'SUCCESS' else data['error']
        print(f"{idx+1:2d} - {data['task_id']} - {data['status']} - {output}")
