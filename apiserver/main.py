from typing import Optional
from typing import Dict

from fastapi import FastAPI
from fastapi import HTTPException

from pydantic import BaseModel

from .storage import JsonFileStorageAdapter

from .storage import AbstractLocationDataStorageAdapter
from .storage import LocationData
from .storage import LocationDataType

from enum import Enum

app = FastAPI(
    title="API-Server for the Data Catalogue"
)

adapter: AbstractLocationDataStorageAdapter = JsonFileStorageAdapter()

#### A NOTE ON IDS
# the id of a dataset is not yet defined, it could be simply generated, it could be based on some hash of the metadata or simple be the name, which would then need to be enforced to be unique
# this might change some outputs of the GET functions that list reistered elements, but will very likely not change any part of the actual API


# list types of data locations, currently datasets (will be provided by the pillars) and targets (possible storage locations for worklfow results or similar)
@app.get("/")
def get_types():
    return [{element.value : "/" + element.value} for element in LocationDataType]
    

# list id and name of every registered dataset for the specified type
@app.get("/{location_data_type}")
def list_datasets(location_data_type : LocationDataType):
    return adapter.getList(location_data_type)

# register a new dataset, the response will contain the new dataset and its id
@app.put("/{location_data_type}")
def add_dataset(location_data_type : LocationDataType, dataset : LocationData):
    usr: str = "testuser"
    return adapter.addNew(location_data_type, dataset, usr)

# returns all information about a specific dataset, identified by id
@app.get("/{location_data_type}/{dataset_id}")
def get_specific_dataset(location_data_type : LocationDataType, dataset_id: str):
    try:
        return adapter.getDetails(location_data_type, dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='The provided id does not exist for this datatype.')

# update the information about a specific dataset, identified by id
@app.put("/{location_data_type}/{dataset_id}")
def update_specific_dataset(location_data_type : LocationDataType, dataset_id: str, dataset : LocationData):
    try:
        return adapter.updateDetails(location_data_type, dataset_id, dataset, usr)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='The provided id does not exist for this datatype.')
