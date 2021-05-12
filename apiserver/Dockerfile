FROM tiangolo/uvicorn-gunicorn:python3.8

LABEL maintainer="Christian Böttcher <c.boettcher@fz-juelich.de>"

RUN mkdir -p /app/app/data
RUN mkdir -p /app/app/storage

RUN apt update && apt upgrade -y

RUN pip install --no-cache-dir fastapi

COPY ./__init__.py /app/app/
COPY ./main.py /app/app/
COPY ./storage/JsonFileStorageAdapter.py /app/app/storage/
COPY ./storage/LocationStorage.py /app/app/storage/
COPY ./storage/__init__.py /app/app/storage/