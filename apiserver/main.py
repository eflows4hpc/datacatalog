from datetime import timedelta
from enum import Enum
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.param_functions import Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .config import ApiserverSettings
from .security import (ACCESS_TOKEN_EXPIRES_MINUTES, AbstractDBInterface,
                       JsonDBInterface, Token, User, authenticate_user,
                       create_access_token, get_current_user)
from .storage import (AbstractLocationDataStorageAdapter,
                      JsonFileStorageAdapter, LocationData, LocationDataType)


class ReservedPaths(str, Enum):
    TOKEN = 'token'
    HASH = 'hash'
    AUTH = 'auth'
    ME = 'me'


app = FastAPI(
    title="API-Server for the Data Catalog"
)


settings = ApiserverSettings()
adapter = JsonFileStorageAdapter(settings)
userdb = JsonDBInterface(settings)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=ReservedPaths.TOKEN)

# A NOTE ON IDS
# the id of a dataset is not yet defined, it could be simply generated,
# it could be based on some hash of the metadata or simple be the name,
# which would then need to be enforced to be unique
#
# this might change some outputs of the GET functions that list
# reistered elements, but will very likely not change any part of the actual API


def my_user(token=Depends(oauth2_scheme)):
    return get_current_user(token, userdb)

def my_auth(form_data: OAuth2PasswordRequestForm = Depends()):
    return authenticate_user(userdb, form_data.username, form_data.password)
    
@app.get("/")
async def get_types():
    # list types of data locations, currently datasets
    # (will be provided by the pillars) and targets (possible storage
    #  locations for worklfow results or similar)
    return [{element.value: "/" + element.value} for element in LocationDataType]


@app.get("/me", response_model=User)
async def read_users_me(user=Depends(my_user)):
    # return information about the currently logged in user
    return user


@app.post("/token", response_model=Token)
async def login_for_access_token(user=Depends(my_auth)):
    # authenticate with username/ password, return an auth-token
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
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/{location_data_type}")
async def list_datasets(location_data_type: LocationDataType):
    # list id and name of every registered dataset for the specified type
    return adapter.get_list(location_data_type)


@app.post("/{location_data_type}")
async def add_dataset(location_data_type: LocationDataType,
                      dataset: LocationData,
                      user: User = Depends(my_user)):
    # register a new dataset, the response will contain the new dataset and its id
    return adapter.add_new(location_data_type, dataset, user.username)


@app.get("/{location_data_type}/{dataset_id}")
async def get_specific_dataset(location_data_type: LocationDataType, dataset_id: str):
    # returns all information about a specific dataset, identified by id
    return adapter.get_details(location_data_type, dataset_id)
    

@app.put("/{location_data_type}/{dataset_id}")
async def update_specific_dataset(location_data_type: LocationDataType,
                                  dataset_id: str, dataset: LocationData,
                                  user: User = Depends(my_user)):
    # update the information about a specific dataset, identified by id
   
    return adapter.update_details(location_data_type, dataset_id, dataset, user.username)
    

@app.delete("/{location_data_type}/{dataset_id}")
async def delete_specific_dataset(location_data_type: LocationDataType,
                                  dataset_id: str,
                                  user: str = Depends(my_user)):
    # delete a specific dataset
    # TODO: 404 is the right answer? 204 could also be the right one
    return adapter.delete(location_data_type, dataset_id, user.username)
    

@app.exception_handler(FileNotFoundError)
async def not_found_handler(request: Request, exc: FileNotFoundError):
    oid=request.path_params.get('dataset_id', '')
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, 
                        content={'message':f"Object {oid} does not exist"})