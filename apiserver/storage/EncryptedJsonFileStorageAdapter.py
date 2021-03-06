from cryptography.fernet import Fernet

from apiserver.config.settings import ApiserverSettings
from .JsonFileStorageAdapter import JsonFileStorageAdapter, LocationDataType

class EncryptedJsonFileStorageAdapter(JsonFileStorageAdapter):

    def encrypt(self, string: str):
        f = Fernet(self.encryption_key)
        return f.encrypt(string.encode()).decode("utf-8")

    def decrypt(self, string: str):
        f = Fernet(self.encryption_key)
        return f.decrypt(string.encode()).decode("utf-8")

    def __init__(self, settings: ApiserverSettings) -> None:
        self.encryption_key = settings.encryption_key
        super().__init__(settings)


    def get_secret_values(self, n_type: LocationDataType, oid:str, usr: str):
        """ get all available secrets (key + value) for this object"""
        encrypted_dict = super().get_secret_values(n_type, oid, usr)
        return {k: self.decrypt(v) for k,v in encrypted_dict.items()}

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
