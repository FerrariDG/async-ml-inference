FROM python:3.7-slim-buster

COPY requirements.txt /api/requirements.txt

WORKDIR /api

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --compile -r requirements.txt && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/* /tmp/* /var/tmp/*

COPY api.py /api/api.py

EXPOSE 5000 6379 5672

CMD uvicorn api:api --host 0.0.0.0 --port 5000
