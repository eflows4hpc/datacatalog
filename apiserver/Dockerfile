FROM tiangolo/uvicorn-gunicorn:python3.8

LABEL maintainer="Christian Böttcher <c.boettcher@fz-juelich.de>"

RUN mkdir -p /app/data

RUN apt update && apt upgrade -y

RUN pip install --no-cache-dir fastapi

COPY ./main.py /app/
COPY ./LocationStorage.py /app/
COPY ./JsonFileStorageAdapter.py /app/