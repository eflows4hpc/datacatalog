from fastapi.exceptions import HTTPException
from JsonFileStorageAdapter import JsonFileStorageAdapter, LocationDataType
from cryptography.fernet import Fernet

from apiserver.config.settings import ApiserverSettings

class EncryptedJsonFileStorageAdapter(JsonFileStorageAdapter):

    def encrypt(self, string: str):
        f = Fernet(self.encryption_key)
        return f.encrypt(string.encode())

    def decrypt(self, string: str):
        f = Fernet(self.encryption_key)
        return f.decrypt(string.encode())
    
    def __init__(self, settings: ApiserverSettings, encryption_key) -> None:
        self.encryption_key = encryption_key
        super().__init__(settings)
    
    
    def get_secret_values(self, n_type: LocationDataType, oid:str, usr: str):
        """ get all available secrets (key + value) for this object"""
        encrypted_dict = super().get_secret_values(n_type, oid, usr)
        decrypted_dict = {}
        for key in encrypted_dict:
            decrypted_dict[key] = self.decrypt(encrypted_dict[key])
        return decrypted_dict

    def add_update_secret(self, n_type: LocationDataType, oid:str, key: str, value: str, usr: str):
        """ add new secrets to an existing object"""
        super().add_update_secret(n_type, oid, key, self.encrypt(value), usr)

    def get_secret(self, n_type: LocationDataType, oid:str, key: str, usr: str):
        """ return the value of the requested secret for the given object"""
        encrypted_secret = super().get_secret(n_type, oid, key, usr)
        return self.decrypt(encrypted_secret)

    def delete_secret(self, n_type: LocationDataType, oid:str, key: str, usr: str):
        """ delete and return the value of the requested secret for the given object"""
        return self.decrypt(super().delete_secret(n_type, oid, key, usr))