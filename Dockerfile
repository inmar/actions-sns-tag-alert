FROM python:3.10-slim-bullseye

RUN apt-get update \
 && apt-get install -y git

RUN pip install --no-cache-dir -U pip wheel

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENTRYPOINT ["/app/action.py"]
