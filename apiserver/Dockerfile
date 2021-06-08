FROM python:3.9-slim

LABEL maintainer="Christian Böttcher <c.boettcher@fz-juelich.de>"
EXPOSE 8000

RUN mkdir -p /app/data
RUN mkdir -p /app/apiserver

RUN pip install "fastapi==0.63.0" \
"requests==2.25.1" \
"uvicorn==0.13.4" \
"python-dotenv==0.17.1" \
"python-multipart==0.0.5" \
"python-jose[cryptography]==3.2.0" \
"passlib[bcrypt]==1.7.4"

ADD . /app/apiserver

# set data directory properly for the docker container
RUN sed -i 's_./app/data_/app/data_g' /app/apiserver/config.env && sed -i 's_./app/userdb.json_/app/userdb.json_g' /app/apiserver/config.env

WORKDIR /app

ENTRYPOINT ["uvicorn", "--host", "0.0.0.0", "apiserver:app"]