# DataCatalog

This is Data Catalog for eFlows4HPC project

This work has been supported by the eFlows4HPC project, contract #955558. This project has received funding from the European High-Performance Computing Joint Undertaking (JU) under grant agreement No 955558. The JU receives support from the European Union’s Horizon 2020 research and innovation programme and Spain, Germany, France, Italy, Poland, Switzerland, Norway.


Find architecture in [arch](arch/arch.adoc) folder. 


## Frontend Server for the Data Catalog

[This](frontend/) part is the frontend for the Data Catalog. It will be the user interface, so that no one is forced to manually do http calls to the api. Since the content is managed by the [api-server](apiserver/), this can be deployed as a static website, containing only html, css and javascript. To make the different pages more uniform and avoid duplicate code, the static pages will be generated by the [jinja2](https://jinja.palletsprojects.com/en/3.0.x/templates/) template engine.

To compile the static pages to the `./site/` directory (will be created if required), simply run 
```bash
pip install -r requirements.txt
python frontend/createStatic.py
```

The site can then be deployed to any webserver that is capable of serving files, as no other server functionality is strictly required. However, in a proper deployment, access and certificates should be considered.

For development (and only for development), an easy way to deploay a local server is
```shell
python -m http.server <localport> --directory site/
```

## API-Server for the Data Catalog

[This](apiserver/) part is the the API-server for the Data Catalog, which will provide the backend functionality.

It is implemented via [fastAPI](https://fastapi.tiangolo.com/) and provides an api documentation via openAPI.

For deployment via [docker](https://www.docker.com/), a docker image is included. 

### Security

Certain operations will only be possible, if the request is authenticated. The API has an endpoint at `/token` where a username/password login is possible. The endpoint will return a token, which is valid for 1 hour. This token has to be provided with every api call that requires authentication. Currently, these calls are `GET /me` - `PUT /dataset` - `PUT /dataset/dataset-id` - `DELETE /dataset/dataset-id`. The passwords are stored as bcrypt hashes and are not visible to anyone.

A CLI is provided for server admins to add new users. It will soon be extended to allow direct hash entry, so that the user does not have to provide their password in clear text.

For testing, a default userdb.json is provided with a single user "testuser" with the password "test".

### API Documentation

If the api-server is running, you can see the documentation at `<server-url>/docs` or `<server-url>/redoc`.

These pages can also be used as a clunky frontend, allowing the authentication and execution of all api functions.


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

First ensure that the `pytest` package is installed (It is included in the `testing_requirements.txt`).

Tests are located in the `apiserver_tests` directory. They can be executed by simply running `pytest` while in the project folder. You can also use
nose for test (also included in `testing_requirements.txt`), for instance for tests with coverage report in html format run following:
```bash
nosetests --with-coverage --cover-package=apiserver --cover-html
```

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
docker run -d --name <container name> -p 127.0.0.1:<local_port>:8000 datacalog-apiserver
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
