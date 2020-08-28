FROM python:3.7-slim-buster

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN apt-get update -yqq && \
    apt-get -yqq install libsndfile1 --no-install-recommends && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --compile -r requirements.txt && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/* /tmp/* /var/tmp/*

COPY . /app

EXPOSE 6379 5672

CMD celery worker -A worker.audio --loglevel=INFO
