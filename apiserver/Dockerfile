FROM python:3.9-slim
LABEL maintainer="Christian Böttcher <c.boettcher@fz-juelich.de>"
EXPOSE 8000
VOLUME /app/data
ADD ./apiserver/ /app/apiserver
ADD ./requirements.txt /app/apiserver/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /app/apiserver/requirements.txt
# set data directory properly for the docker container
RUN sed -i 's_./app/data_/app/data_g' /app/apiserver/config.env && sed -i 's_./app/userdb.json_/app/userdb.json_g' /app/apiserver/config.env
WORKDIR /app
ENTRYPOINT ["uvicorn", "--host", "0.0.0.0", "apiserver:app"]