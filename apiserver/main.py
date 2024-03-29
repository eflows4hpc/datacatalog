"""
Main module of data catalog api
"""
import logging
import os
from datetime import timedelta, datetime
from enum import Enum
from typing import Dict, List
from functools import wraps

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.param_functions import Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from authlib.integrations.starlette_client import OAuth

from pydantic import UUID4
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from apiserver.security.user import Secret

from .config import ApiserverSettings
from .security import (ACCESS_TOKEN_EXPIRES_MINUTES, JsonDBInterface, Token,
                       User, authenticate_user, create_access_token,
                       get_current_user)
from .storage import JsonFileStorageAdapter, LocationData, LocationDataType, EncryptedJsonFileStorageAdapter

log = logging.getLogger(__name__)


class ReservedPaths(str, Enum):
    TOKEN = 'token'
    HASH = 'hash'
    AUTH = 'auth'
    ME = 'me'

DOTENV_FILE_PATH_VARNAME = "DATACATALOG_API_DOTENV_FILE_PATH"
DOTENV_FILE_PATH_DEFAULT = "apiserver/config.env"

app = FastAPI(
    title="API-Server for the Data Catalogue",
    root_path= os.getenv("DATACAT_ROOT_PATH", "")
)

app.add_middleware(SessionMiddleware, secret_key="secret-string") #  TODO generate secret string during startup

origins = [
    "https://datacatalog.fz-juelich.de",
    "https://datacatalogue.eflows4hpc.eu",
    "https://zam10059.zam.kfa-juelich.de",
    "https://zam10036.zam.kfa-juelich.de",
    "http://datacatalog.fz-juelich.de",
    "http://datacatalogue.eflows4hpc.eu",
    "http://zam10059.zam.kfa-juelich.de",
    "http://zam10036.zam.kfa-juelich.de"
]

app.add_middleware(CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)

# if env variable is set, get config .env filepath from it, else use default
dotenv_file_path = os.getenv(DOTENV_FILE_PATH_VARNAME, DOTENV_FILE_PATH_DEFAULT)


settings = ApiserverSettings(_env_file=dotenv_file_path)

if settings.encryption_key is not None and settings.encryption_key:
    log.debug("Using encrypted secrets backend.")
    # let the error break the server (clearly an encrypted backed is requested, 
    # fallback to non encrypted is not good)
    adapter = EncryptedJsonFileStorageAdapter(settings)
else:
    adapter = JsonFileStorageAdapter(settings)

userdb = JsonDBInterface(settings)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=ReservedPaths.TOKEN)

oauth = OAuth()
oauth.register(
    name='keycloak',
    client_id=settings.client_id,
    server_metadata_url=settings.server_metadata_url,
    client_secret=settings.client_secret,
    client_kwargs={
        'scope' : 'openid email profile eflows'
    }
)

log.info("Loaded the following settings: data directory = %s | userdb location = %s", settings.json_storage_path, settings.userdb_path)

def my_user(token=Depends(oauth2_scheme)):
    return get_current_user(token, userdb)

def my_auth(form_data: OAuth2PasswordRequestForm = Depends()):
    return authenticate_user(userdb, form_data.username, form_data.password)

def secrets_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        user = kwargs.get('user', None)
        if user is None or not user.has_secrets_access:
            raise HTTPException(403)
        return await func(*args, **kwargs)
    return wrapper

@app.get("/sso_login")
async def sso_login(request: Request):
    """redirect to keycloak for login, obtain keycloak token via cookie"""
    redirect_url = request.url_for('sso_token')
    log.debug("redirect_uri " + redirect_url)
    return await oauth.keycloak.authorize_redirect(request, redirect_url)

@app.get("/sso_token")
async def sso_token(request: Request):
    """obtain keycloak token via cookie, generate custom token and return it"""
    token = await oauth.keycloak.authorize_access_token(request)

    user = await oauth.keycloak.userinfo(token=token)

    persistent_identifier = token["userinfo"]["sub"]
    log.debug(str(user))

    # now we have an authenticated user
    # check if the user is in the database, if not:
    # check for the roles that are in the IdP and create accordingly (may result in no new user creation and a return of a 403)
    # generate a datacat auth token for the user that identical to a token received from /token
    # store it in the session cookie, return it via a redirect to the user frontend
    email = user['email']


    if userdb.get(persistent_identifier) is None:
        # check if user should be added
        access_group = "datacat_write"
        userdb.add_external_auth_user(persistent_identifier, email)

            
    datacat_user = userdb.get(persistent_identifier)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    access_token = create_access_token(
        data={"sub": datacat_user.username}, expires_delta=access_token_expires
    )
    log.debug("Externally authenticed User: '%s' requested /sso_token", datacat_user.username)

    # set token in cookie, this can then be extractet via the frontend javascript
    response = RedirectResponse("./login.html?external_auth=True")
    response.set_cookie(
        key="datacat_auth_token", value=access_token, secure=True, expires=datetime.utcnow()+timedelta(minutes=5)
    ) 

    return response

@app.get("/me", response_model=User)
async def read_users_me(user=Depends(my_user)):
    """return information about the currently logged in user"""
    log.debug("Authenticed User: '%s' requested /me", user.username)
    return user


@app.post("/token", response_model=Token)
async def login_for_access_token(user=Depends(my_auth)):
    """authenticate with username/ password, return an auth-token"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    log.debug("Authenticed User: '%s' requested /token", user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/", response_model=List[dict[str, str]])
async def get_types(request: Request = None, element_numbers: bool = False):
    """
    list types of data locations, currently datasets
    (will be provided by the pillars) and targets (possible storage
    locations for worklfow results or similar)
    """
    try:
        accept_header = request.headers['Accept']
    except KeyError:
        accept_header = "application/json"
    accept_json = "application/json"
    accept_html = "text/html"
    default_return = [{element.value: "/" + element.value} for element in LocationDataType]
    element_number_return = [{element.value : len(adapter.get_list(element))} for element in LocationDataType]
    redirect_return = RedirectResponse(url='/index.html')

    if (element_numbers):
        return element_number_return

    # uses first of json and html that is in the accept header; returns json if neither is found
    json_pos = accept_header.find(accept_json)
    html_pos = accept_header.find(accept_html)

    if json_pos == -1:
        json_pos = len(accept_header)
    if html_pos == -1:
        html_pos = len(accept_header)

    if html_pos < json_pos:
        log.debug("Browser was redirected to index.html")
        return redirect_return

    return default_return


@app.get("/{location_data_type}", response_model=List[List[str]])
async def list_datasets(location_data_type: LocationDataType, search: str = None, name: str = None, url: str = None, has_key: List[str] = Query(default=None), page: int = None, page_size: int = 25, element_numbers: bool = False):
    """
    list id and name of all matching registered datasets for the specified type\n
    name: has to be contained in the name of the object\n
    url: has to be contained in the url of the object\n
    has_key: has to contain the exact key in the metadata\n
    search: has to contain this term in any field of the object (name, url, metadata key or metadata value)\n
    page: \n
    page_size: \n
    element_numbers: \n
    """
    datasets = adapter.get_list(location_data_type)

    if name:
        tmpset = []
        for element in datasets:
            if name.lower() in element[0].lower():
                tmpset.append(element)
        datasets = tmpset

    if url:
        tmpset = []
        for element in datasets:
            if url.lower() in adapter.get_details(location_data_type, element[1]).url.lower():
                tmpset.append(element)
        datasets = tmpset
    
    if has_key:
        tmpset = []
        for element in datasets:
            if set(has_key).issubset(set(adapter.get_details(location_data_type, element[1]).metadata.keys())):
                tmpset.append(element)
        datasets = tmpset

    if search:
        tmpset = []
        for element in datasets:
            if search.lower() in element[0].lower():
                tmpset.append(element)
                continue
            details = adapter.get_details(location_data_type, element[1])
            if search.lower() in details.url.lower():
                tmpset.append(element)
                continue
            metadata_match = False
            for key, value  in details.metadata.items():
                if search.casefold() in key.casefold() or search.casefold() in value.casefold():
                    metadata_match = True
                    break
            if metadata_match:
                tmpset.append(element)
                continue

            
        datasets = tmpset

    if (element_numbers):
        return [[location_data_type.value, str(len(datasets))]]

    sorted_datasets = sorted(datasets, key=lambda x: (x[0], x[1]))

    if (page):
        # get page_size elements at index (page-1) * page_size
        index = (page - 1) * page_size
        if index >= len(sorted_datasets):
            return []
        elif index + page_size > len(sorted_datasets):
            return sorted_datasets[index:]
        else:
            return sorted_datasets[index:index+page_size]
    else:
        return sorted_datasets
    


@app.get("/{location_data_type}/{dataset_id}", response_model=LocationData)
async def get_specific_dataset(location_data_type: LocationDataType, dataset_id: UUID4):
    """returns all information about a specific dataset, identified by id"""
    return adapter.get_details(location_data_type, str(dataset_id))

@app.post("/{location_data_type}")
async def add_dataset(location_data_type: LocationDataType,
                      dataset: LocationData,
                      user: User = Depends(my_user)):
    """register a new dataset, the response will contain the new dataset and its id"""
    log.debug("Authenticed User: '%s' created new /%s", user.username, location_data_type.value)
    return adapter.add_new(location_data_type, dataset, user.username)


@app.put("/{location_data_type}/{dataset_id}")
async def update_specific_dataset(location_data_type: LocationDataType,
                                  dataset_id: UUID4, dataset: LocationData,
                                  user: User = Depends(my_user)):
    """update the information about a specific dataset, identified by id"""
    log.debug("Authenticed User: '%s' modified /%s/%s", user.username, location_data_type.value, dataset_id)
    return adapter.update_details(location_data_type, str(dataset_id), dataset, user.username)

@app.delete("/{location_data_type}")

async def delete_multiple_datasets(location_data_type: LocationDataType,
                                  dataset_ids: List[UUID4],
                                  user: User = Depends(my_user)
                                  ):
    """
    Attempts deletion of every sent dataset. If it fails for any of the sent datasets (for example due to a not found error), the attempts for the other datasets will still be made. 
    This may result in an incomplete delete and may return error codes. 
    """
    log.debug("Authenticed User: '%s' deleted multiple %s objects: %s", user.username, location_data_type.value, str(dataset_ids))
    other_error = False
    for oid in dataset_ids:
        try:
            adapter.delete(location_data_type, str(oid), user.username)
        except:
            other_error = True
    if other_error:
        raise HTTPException(500, "Some error occured during the bulk deletion. Some, None or all elements may have been deleted") # TODO better error identification and message
    return JSONResponse({'message':'Bulk deletion successful.'})

@app.delete("/{location_data_type}/{dataset_id}")
async def delete_specific_dataset(location_data_type: LocationDataType,
                                  dataset_id: UUID4,
                                  user: User = Depends(my_user)):
    """delete a specific dataset"""
    # TODO: 404 is the right answer? 204 could also be the right one
    log.debug("Authenticed User: '%s' deleted /%s/%s", user.username, location_data_type.value, dataset_id)
    return adapter.delete(location_data_type, str(dataset_id), user.username)

@app.get("/{location_data_type}/{dataset_id}/secrets")
@secrets_required
async def list_dataset_secrets(location_data_type: LocationDataType,
                                  dataset_id: UUID4,
                                  user: User = Depends(my_user)):
    """list the secrets of a specific dataset"""
    log.debug("Authenticed User: '%s' listed the secrets of /%s/%s", user.username, location_data_type.value, dataset_id)
    return adapter.list_secrets(location_data_type, dataset_id, user)

@app.get("/{location_data_type}/{dataset_id}/secrets/{key}")
@secrets_required
async def get_dataset_secret(location_data_type: LocationDataType,
                                  dataset_id: UUID4,
                                  key: str,
                                  user: User = Depends(my_user)):
    """get the secret of a specific dataset"""
    log.debug("Authenticed User: '%s' listed the secret %s of /%s/%s", user.username, key, location_data_type.value, dataset_id)
    return adapter.get_secret(location_data_type, dataset_id, key, user)

# differs from .../secrets by also returning the values in a dict
@app.get("/{location_data_type}/{dataset_id}/secrets_values")
@secrets_required
async def list_dataset_secrets(location_data_type: LocationDataType, dataset_id: UUID4, user: User = Depends(my_user)):
    """list the secrets and valuesof a specific dataset"""
    log.debug("Authenticed User: '%s' listed the secrets (key and value) of /%s/%s", user.username, location_data_type.value, dataset_id)
    return adapter.get_secret_values(location_data_type, dataset_id, user)


@app.post("/{location_data_type}/{dataset_id}/secrets")
@secrets_required
async def add_update_dataset_secret(location_data_type: LocationDataType,
                                  dataset_id: UUID4,
                                  secret: Secret,
                                  user: User = Depends(my_user)):
    """add or update a secrets to a specific dataset"""
    log.debug("Authenticed User: '%s' added or updated the secret %s of /%s/%s", user.username, secret.key, location_data_type.value, dataset_id)
    return adapter.add_update_secret(location_data_type, dataset_id, secret.key, secret.secret, user)


@app.delete("/{location_data_type}/{dataset_id}/secrets/{key}")
@secrets_required
async def get_dataset_secrets(location_data_type: LocationDataType,
                                  dataset_id: UUID4,
                                  key: str,
                                  user: User = Depends(my_user)):
    """delete a secret from a specific dataset"""
    log.debug("Authenticed User: '%s' deleted the secret %s from /%s/%s", user.username, key, location_data_type.value, dataset_id)
    return adapter.delete_secret(location_data_type, dataset_id, key, user)

@app.exception_handler(FileNotFoundError)
async def not_found_handler(request: Request, ex: FileNotFoundError):
    _ =request.path_params.get('dataset_id', '')
    log.error("File not found translated %s", ex)
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                        content={'message':'Object does not exist'})
