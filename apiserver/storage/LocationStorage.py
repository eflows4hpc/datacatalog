
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

#
'''
This is an abstract storage adapter for storing information about datasets, storage targets and similar things.
It can easily be expanded to also store other data (that has roughly similar metadata), just by expanding the LocationDataType Enum.

In general, all data is public. This means, that the adapter does not do any permission checking, except when explicitly asked via the checkPerm function.
The caller therefore has to manually decide when to check for permissions, and not call any function unless it is already authorized (or does not need any authorization).

The usr: str (the user id) that is required for several functions, is a unique and immutable string, that identifies the user. This can be a verified email or a user name. 
The management of authentication etc. is done by the caller, this adapter assumes that the user id fulfills the criteria.
Permissions are stored as a list of user ids, and every id is authorized for full access.
'''
class AbstractLocationDataStorageAdapter:
    # get a list of all LocationData Elements with the provided type, as pairs of {name : id}
    def getList(self, type: LocationDataType):
        raise NotImplementedError()

    # add a new element of the provided type, assign and return the id and the new data as {id : LocationData}
    def addNew(self, type: LocationDataType, data: LocationData, usr: str):
        raise NotImplementedError()

    # return the LocationData of the requested object (identified by id and type)
    def getDetails(self, type: LocationDataType, id: str):
        raise NotImplementedError()

    # change the details of the requested object, return {id : newData}
    def updateDetails(self, type:LocationDataType, id:str, data: LocationData, usr: str):
        raise NotImplementedError()

    # return the owner of the requested object; if multiple owners are set, return them is a list
    def getOwner(self, type: LocationDataType, id: str):
        raise NotImplementedError()

    # check if the given user has permission to change the given object
    def checkPerm(self, type: LocationDataType, id: str, usr: str):
        raise NotImplementedError()

    # add user to file perm
    def addPerm(self, type: LocationDataType, id: str, usr: str):
        raise NotImplementedError()

    # remove user from file perm
    def rmPerm(self, type: LocationDataType, id: str, usr: str):
        raise NotImplementedError()
