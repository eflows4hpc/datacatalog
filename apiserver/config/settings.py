from pydantic import BaseSettings

DEFAULT_JSON_FILEPATH: str = "./app/data"

## Additional Settings can be made available by adding them as properties to this class
# At launch they will be read from environment variables (case-INsensitive)

class ApiserverSettings(BaseSettings):
    json_storage_path: str = DEFAULT_JSON_FILEPATH
    userdb_path: str = None
    encryption_key: str = None
    client_id: str = None
    client_secret: str = None
    server_metadata_url: str = None

    class Config:
        env_prefix: str = "datacatalog_apiserver_"
        env_file: str = "apiserver/config.env"