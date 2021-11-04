"""
Main module of data catalog api
"""
import logging
import os
from datetime import timedelta
from enum import Enum
from typing import List

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.param_functions import Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from pydantic import UUID4
from starlette.responses import RedirectResponse

from .config import ApiserverSettings
from .security import (ACCESS_TOKEN_EXPIRES_MINUTES, JsonDBInterface, Token,
                       User, authenticate_user, create_access_token,
                       get_current_user)
from .storage import JsonFileStorageAdapter, LocationData, LocationDataType, verify_oid

log = logging.getLogger(__name__)


class ReservedPaths(str, Enum):
    TOKEN = 'token'
    HASH = 'hash'
    AUTH = 'auth'
    ME = 'me'

DOTENV_FILE_PATH_VARNAME = "DATACATALOG_API_DOTENV_FILE_PATH"
DOTENV_FILE_PATH_DEFAULT = "apiserver/config.env"

app = FastAPI(
    title="API-Server for the Data Catalog"
)

# if env variable is set, get config .env filepath from it, else use default
dotenv_file_path = os.getenv(DOTENV_FILE_PATH_VARNAME, DOTENV_FILE_PATH_DEFAULT)

settings = ApiserverSettings(_env_file=dotenv_file_path)
adapter = JsonFileStorageAdapter(settings)
userdb = JsonDBInterface(settings)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=ReservedPaths.TOKEN)

log.info("Loaded the following settings: data directory = %s | userdb location = %s", settings.json_storage_path, settings.userdb_path)

def my_user(token=Depends(oauth2_scheme)):
    return get_current_user(token, userdb)

def my_auth(form_data: OAuth2PasswordRequestForm = Depends()):
    return authenticate_user(userdb, form_data.username, form_data.password)

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
async def get_types(request: Request = None):
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
    redirect_return = RedirectResponse(url='/index.html')

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
    else:
        return default_return


@app.get("/{location_data_type}")
async def list_datasets(location_data_type: LocationDataType):
    """list id and name of every registered dataset for the specified type"""
    return adapter.get_list(location_data_type)


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


@app.delete("/{location_data_type}/{dataset_id}")
async def delete_specific_dataset(location_data_type: LocationDataType,
                                  dataset_id: UUID4,
                                  user: str = Depends(my_user)):
    """delete a specific dataset"""
    # TODO: 404 is the right answer? 204 could also be the right one
    log.debug("Authenticed User: '%s' deleted /%s/%s", user.username, location_data_type.value, dataset_id)
    return adapter.delete(location_data_type, str(dataset_id), user.username)

@app.get("/{location_data_type}/{dataset_id}/secrets")
async def list_dataset_secrets(location_data_type: LocationDataType,
                                  dataset_id: UUID4,
                                  user: str = Depends(my_user)):
    """list the secrets of a specific dataset"""
    # TODO log
    if userdb.get(user).has_secrets_access:
        return adapter.list_secrets(location_data_type, dataset_id, user)
    else:
        raise HTTPException(403)

@app.get("/{location_data_type}/{dataset_id}/secrets/{key}")
async def get_dataset_secret(location_data_type: LocationDataType,
                                  dataset_id: UUID4,
                                  key: str,
                                  user: str = Depends(my_user)):
    """get the secrets of a specific dataset"""
    # TODO log
    if userdb.get(user).has_secrets_access:
        return adapter.get_secret(location_data_type, dataset_id, key, user)
    else:
        raise HTTPException(403)

@app.put("/{location_data_type}/{dataset_id}/secrets/{key}")
async def add_update_dataset_secret(location_data_type: LocationDataType,
                                  dataset_id: UUID4,
                                  key: str,
                                  value: str,
                                  user: str = Depends(my_user)):
    """get the secrets of a specific dataset"""
    # TODO log
    if userdb.get(user).has_secrets_access:
        return adapter.add_update_secret(location_data_type, dataset_id, key, value, user)
    else:
        raise HTTPException(403)

@app.delete("/{location_data_type}/{dataset_id}/secrets/{key}")
async def get_dataset_secrets(location_data_type: LocationDataType,
                                  dataset_id: UUID4,
                                  key: str,
                                  user: str = Depends(my_user)):
    """delete a secret of a specific dataset"""
    # TODO log
    if userdb.get(user).has_secrets_access:
        return adapter.delete_secret(location_data_type, dataset_id, key, user)
    else:
        raise HTTPException(403)



@app.exception_handler(FileNotFoundError)
async def not_found_handler(request: Request, ex: FileNotFoundError):
    _ =request.path_params.get('dataset_id', '')
    log.error("File not found translated %s", ex)
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                        content={'message':'Object does not exist'})
