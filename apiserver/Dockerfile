FROM python:3.9-slim
LABEL maintainer="Christian Böttcher <c.boettcher@fz-juelich.de>"
RUN useradd --create-home apiserver
WORKDIR /home/apiserver
USER apiserver

EXPOSE 8000
RUN mkdir -p ./mnt/data
VOLUME /home/apiserver/mnt/
COPY ./requirements.txt ./requirements.txt
RUN python3 -m pip install --upgrade pip && python3 -m pip install --user --no-cache-dir -r ./requirements.txt
ENV PATH="/home/apiserver/.local/bin/:${PATH}"
# set data directory properly for the docker container
COPY --chown=apiserver ./apiserver/ ./apiserver
RUN sed -i 's_./app/data_./mnt/data_g' ./apiserver/config.env && sed -i 's_./app/userdb.json_./mnt/userdb.json_g' ./apiserver/config.env && sed -i 's_./app/apiserver.log_./mnt/apiserver.log_g' ./apiserver/log_conf.yaml
ENTRYPOINT ["uvicorn", "--host", "0.0.0.0", "--log-level", "debug", "--log-config=./apiserver/log_conf.yaml", "apiserver:app"]
