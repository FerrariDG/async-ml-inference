FROM python:3.7-slim-buster

COPY requirements.txt /client/requirements.txt

WORKDIR /client

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --compile -r requirements.txt && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/* /tmp/* /var/tmp/*

COPY client.py /client/client.py

EXPOSE 5000

CMD python client.py
