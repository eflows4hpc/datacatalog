# API-Server for the Data Catalog

This is the API-server for the Data Catalog, which will provide the backend functionality.

It is implemented via [fastAPI](https://fastapi.tiangolo.com/) and provides an api documentation via openAPI.

For deployment via [docker](https://www.docker.com/), a docker image is included. 

## API Documentation

If the api-server is running, you can see the documentation at `<server-url>/docs` or `<server-url>/redoc`.


## Running without docker
First ensure that your python version is 3.6 or newer.

Then, if they are not yet installed on your machine, install the following two packages via pip:

```bash
pip install fastapi
pip install uvicorn[standard]
```

To start the server, run
```bash
uvicorn main:app --reload
```

Withour any other options, this starts your server on `<localhost:8000>`.
The `--reload` option ensures, that any changes to the `api-server.py` will cause an immediate reload of the server, which es especially interesting during development. If this is not required, just don't include the option.

More information about uvicorn settings (including information about how to bind to other network interfaces or ports) can be found [here](https://www.uvicorn.org/settings/).


## Using the docker image

### Building the docker image

To build the docker image of the current version, simply run

```bash
docker built -t datacatalog-apiserver .
```
while in the same directory as the Dockerfile.

`datacatalog-apiserver` is a local tag to identify the built docker image.

### Running the docker image

To run the docker image in a local container, run 
```bash
docker run -d --name <container name> -p localhost:<local_port>:80 datacalog-apiserver
```

`<container name>` is the name of your container, that can be used to refer to it with other docker commands.

`<local_port>` is the port of your local machine, which will be forwarded to the docker container. For example, if it is set to `8080`, you will be able to reach the api-server at http://localhost:8080.

### Stopping the docker image

To stop the docker image, run
```bash
docker stop <container name>
```

Note, that this will only stop the container, and not delete it fully. To do that, run

```bash
docker rm <container name>
```

For more information about docker, please see the [docker docs](https://docs.docker.com)