# DataCatalog

This is Data Catalog for eFlows4HPC project

Find architecture in [arch](arch/arch.adoc) folder. 


## API-Server for the Data Catalog

[This](apiserver/) part is the the API-server for the Data Catalog, which will provide the backend functionality.

It is implemented via [fastAPI](https://fastapi.tiangolo.com/) and provides an api documentation via openAPI.

For deployment via [docker](https://www.docker.com/), a docker image is included. 

### API Documentation

If the api-server is running, you can see the documentation at `<server-url>/docs` or `<server-url>/redoc`.


### Running without docker
First ensure that your python version is 3.6 or newer.

Then, if they are not yet installed on your machine, install the requirements via pip:

```bash
pip install -r requirements.txt
```

To start the server, run
```bash
uvicorn apiserver:app --reload --reload-dir apiserver
```
while in the project root directory.

Without any other options, this starts your server on `<localhost:8000>`.
The `--reload --reload-dir apiserver` options ensure, that any changes to files in the `apiserver`-directory will cause an immediate reload of the server, which is especially useful during development. If this is not required, just don't include the options.

More information about uvicorn settings (including information about how to bind to other network interfaces or ports) can be found [here](https://www.uvicorn.org/settings/).

### Testing

First ensure that the `pytest` package is installed (It is included in the `requirements.txt`).

Tests are located in the `apiserver_tests` directory. They can be executed by simply running `pytest` while in the project folder.

If more test-files should be added, they should be named with a `test_` prefix and put into a similarily named folder, so that they can be auto-detected.

The `context.py` file helps with importing the apiserver-packages, so that the tests function independent of the local python path setup.




### Using the docker image

#### Building the docker image

To build the docker image of the current version, simply run

```bash
docker build -t datacatalog-apiserver ./apiserver
```
while in the project root directory.

`datacatalog-apiserver` is a local tag to identify the built docker image. You can change it if you want.

#### Running the docker image

To run the docker image in a local container, run 
```bash
docker run -d --name <container name> -p 127.0.0.1:<local_port>:80 datacalog-apiserver
```

`<container name>` is the name of your container, that can be used to refer to it with other docker commands.

`<local_port>` is the port of your local machine, which will be forwarded to the docker container. For example, if it is set to `8080`, you will be able to reach the api-server at http://localhost:8080.

#### Stopping the docker image

To stop the docker image, run
```bash
docker stop <container name>
```

Note, that this will only stop the container, and not delete it fully. To do that, run

```bash
docker rm <container name>
```

For more information about docker, please see the [docker docs](https://docs.docker.com)