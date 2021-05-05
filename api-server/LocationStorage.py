
from pydantic import BaseModel

from typing import Optional
from typing import Dict
from enum import Enum

class LocationDataType(Enum):
    DATASET: str = 'dataset'
    STORAGETARGET: str = 'storage_target'

class LocationData(BaseModel):
    name: str
    url: str
    metadata: Optional[Dict[str, str]]


class AbstractLocationDataStorageAdapter:
    def getList(self, type: LocationDataType):
        raise NotImplementedError()

    def addNew(self, type: LocationDataType, data: LocationData):
        raise NotImplementedError()

    def getDetails(self, type: LocationDataType, id: str):
        raise NotImplementedError()

    def updateDetails(self, type:LocationDataType, id:str, data: LocationData):
        raise NotImplementedError()
