
from enum import Enum
from typing import Dict, Optional, List

from pydantic import BaseModel


class LocationDataType(Enum):
    DATASET = 'dataset'
    STORAGETARGET = 'storage_target'
    AIRFLOW_CONNECTIONS = 'airflow_connections'


class LocationData(BaseModel):
    name: str
    url: str
    metadata: Optional[Dict[str, str]]


class AbstractLocationDataStorageAdapter: # pragma: no cover
    """
    This is an abstract storage adapter for storing information about datasets,
    storage targets and similar things. It can easily be expanded to also store
    other data (that has roughly similar metadata), just by expanding
    the `LocationDataType` Enum.

    In general, all data is public. This means, that the adapter does not
    do any permission checking, except when explicitly asked via the `checkPerm`
    function. The caller therefore has to manually decide when to check for
    permissions, and not call any function unless it is already authorized
    (or does not need any authorization).

    The usr: str (the user id) that is required for several functions, is
    a unique and immutable string, that identifies the user. This can be a
    verified email or a user name. The management of authentication etc. is
    done by the caller, this adapter assumes that the user id fulfills the criteria.
    Permissions are stored as a list of user ids, and every id is authorized for full access.
    """

    def get_list(self, n_type: LocationDataType) -> List:
        """Get a list of all LocationData Elements with the provided type, as pairs of {name : id}"""

        raise NotImplementedError() 
    
    def add_new(self, n_type: LocationDataType, data: LocationData, user_name: str):
        """
        add a new element of the provided type, assign and return the id and
        the new data as {id : LocationData}
        """

        raise NotImplementedError()

    def get_details(self, n_type: LocationDataType, oid: str):
        """ return the LocationData of the requested object (identified by oid and type)"""
        raise NotImplementedError()

    def update_details(self, n_type: LocationDataType, oid: str, data: LocationData, usr: str):
        """ change the details of the requested object, return {oid : newData}"""
        raise NotImplementedError()

    def delete(self, n_type: LocationDataType, oid: str, usr: str):
        """ deletes given resource"""
        raise NotImplementedError()

    def list_secrets(self, n_type: LocationDataType, oid:str, usr: str):
        """ list all available secrets for this object"""
        raise NotImplementedError()
    
    def get_secret_values(self, n_type: LocationDataType, oid:str, usr: str):
        raise NotImplementedError()
    
    def add_update_secret(self, n_type: LocationDataType, oid:str, key: str, value: str, usr: str):
        """ add new secrets to an existing object"""
        raise NotImplementedError()

    def get_secret(self, n_type: LocationDataType, oid:str, key: str, usr: str):
        """ return the value of the requested secret for the given object"""
        raise NotImplementedError()

    def delete_secret(self, n_type: LocationDataType, oid:str, key: str, usr: str):
        """ delete and return the value of the requested secret for the given object"""
        raise NotImplementedError()

    def get_owner(self, n_type: LocationDataType, oid: str):
        """
        return the owner of the requested object; if multiple owners are set,
        return them is a list
        """
        raise NotImplementedError()

    def check_perm(self, n_type: LocationDataType, oid: str, usr: str):
        """ check if the given user has permission to change the given object"""
        raise NotImplementedError()

    def add_perm(self, n_type: LocationDataType, oid: str, usr: str):
        """add user to file perm"""
        raise NotImplementedError()

    def rm_perm(self, n_type: LocationDataType, oid: str, usr: str):
        """remove user from file perm"""
        raise NotImplementedError()
