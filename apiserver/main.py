from typing import Optional
from typing import Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.param_functions import Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from datetime import timedelta

from .storage import JsonFileStorageAdapter
from .storage import AbstractLocationDataStorageAdapter
from .storage import LocationData
from .storage import LocationDataType

from .config import ApiserverSettings

from .security import User, AbstractDBInterface, JsonDBInterface, get_current_user, authenticate_user, create_access_token, Token, ACCESS_TOKEN_EXPIRES_MINUTES

from enum import Enum

class ReservedPaths(Enum):
    TOKEN: str = 'token'
    HASH: str = 'hash'
    AUTH: str = "auth"
    ME: str = "me"


app = FastAPI(
    title="API-Server for the Data Catalog"
)


settings: ApiserverSettings = ApiserverSettings()
adapter: AbstractLocationDataStorageAdapter = JsonFileStorageAdapter(settings)
userdb: AbstractDBInterface = JsonDBInterface(settings)
oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="token")

#### A NOTE ON IDS
# the id of a dataset is not yet defined, it could be simply generated, it could be based on some hash of the metadata or simple be the name, which would then need to be enforced to be unique
# this might change some outputs of the GET functions that list reistered elements, but will very likely not change any part of the actual API


# list types of data locations, currently datasets (will be provided by the pillars) and targets (possible storage locations for worklfow results or similar)
@app.get("/")
async def get_types():
    return [{element.value : "/" + element.value} for element in LocationDataType]

# return information about the currently logged in user
@app.get("/me", response_model=User)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    user = get_current_user(token, userdb)
    return user
# authenticate with username/ password, return an auth-token
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(userdb, form_data.username, form_data.password)
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

# list id and name of every registered dataset for the specified type
@app.get("/{location_data_type}")
async def list_datasets(location_data_type : LocationDataType):
    return adapter.getList(location_data_type)

# register a new dataset, the response will contain the new dataset and its id
@app.put("/{location_data_type}")
async def add_dataset(location_data_type : LocationDataType, dataset : LocationData, token: str = Depends(oauth2_scheme)):
    usr: str = "testuser"
    return adapter.addNew(location_data_type, dataset, usr)

# returns all information about a specific dataset, identified by id
@app.get("/{location_data_type}/{dataset_id}")
async def get_specific_dataset(location_data_type : LocationDataType, dataset_id: str):
    try:
        return adapter.getDetails(location_data_type, dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='The provided id does not exist for this datatype.')

# update the information about a specific dataset, identified by id
@app.put("/{location_data_type}/{dataset_id}")
async def update_specific_dataset(location_data_type : LocationDataType, dataset_id: str, dataset : LocationData, token: str = Depends(oauth2_scheme)):
    usr: str = "testuser"
    try:
        return adapter.updateDetails(location_data_type, dataset_id, dataset, usr)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='The provided id does not exist for this datatype.')

# delete a specific dataset
@app.delete("/{location_data_type}/{dataset_id}")
async def delete_specific_dataset(location_data_type : LocationDataType, dataset_id: str, token: str = Depends(oauth2_scheme)):
    usr: str = "testuser"
    try:
        return adapter.delete(location_data_type, dataset_id, usr)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='The provided id does not exist for this datatype.')