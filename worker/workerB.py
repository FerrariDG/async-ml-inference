from urllib.request import urlopen
from typing import Tuple

from bs4 import BeautifulSoup

from sys import exit

from celery import Celery, states
from celery.exceptions import Ignore


from celery_backend import (
    is_backend_running,
    get_backend_url
)

from celery_broker import (
    is_broker_running,
    get_broker_url
)

if not is_backend_running():
    exit()

if not is_broker_running():
    exit()

euro = Celery("euro", broker=get_broker_url(), backend=get_backend_url())


# Euromillions main URL for scrapy the results
EURO_MAIN_URL = "https://www.euro-millions.com/results/"


@euro.task(bind=True, name="euro.scrappy_result")
def scrappy_result(self, draw_date: str) -> Tuple[int, ...]:
    print('Executing task id {0.id}, args: {0.args!r} kwargs: {0.kwargs!r}'.format(self.request))

    url = EURO_MAIN_URL + draw_date
    try:
        page = urlopen(url)
    except Exception as e:
        self.update_state(
            state=states.FAILURE,
            meta={
                'exc_type': type(e).__name__,
                'exc_message': repr(e),
                "message": f"Unable to open url {url}"
            }
        )
        raise Ignore()

    soup = BeautifulSoup(page, 'html.parser')
    balls = soup.find('div', {'id': 'jsBallOrderCell'})

    if balls is None:
        self.update_state(
            state=states.FAILURE,
            meta={
                'exc_type': type(RuntimeError).__name__,
                'exc_message': repr(RuntimeError),
                "message": "Numbers and Stars not found on the page."
            }
        )
        raise Ignore()

    numbers = []
    stars = []
    for li in balls.findAll('li'):
        if li.attrs['class'][1] == 'ball':
            numbers.append(int(li.getText()))
        elif li.attrs['class'][1] == 'lucky-star':
            stars.append(int(li.getText()))

    return tuple(numbers) + tuple(stars)
