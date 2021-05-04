FROM tiangolo/uvicorn-gunicorn:python3.8

LABEL maintainer="Christian Böttcher <c.boettcher@fz-juelich.de>"

RUN apt update && apt upgrade -y

RUN pip install --no-cache-dir fastapi

COPY ./api-server.py /app/main.py