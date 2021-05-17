FROM tiangolo/uvicorn-gunicorn:python3.8

LABEL maintainer="Christian Böttcher <c.boettcher@fz-juelich.de>"

RUN mkdir -p /app/data
RUN mkdir -p /app/apiserver

RUN apt update && apt upgrade -y

RUN pip install --no-cache-dir fastapi

ADD . /app/apiserver
COPY ./config.env /app/apiserver/config.env

# This RUN creates a python file that contains the fastapi app, in a location that is expected by the base docker image
# This avoids naming conflicts with the packages in the project folder
RUN echo "from apiserver.main import app" > /app/main.py

# set data directory properly for the docker container
RUN sed -i 's_./app/data_/app/data_g' /app/apiserver/config.env