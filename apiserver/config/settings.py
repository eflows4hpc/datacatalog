from pydantic import BaseSettings

DEFAULT_JSON_FILEPATH: str = "./app/data"

## Additional Settings can be made available by adding them as properties to this class
# At launch they will be read from environment variables (case-INsensitive)

class Settings(BaseSettings):
    datacatalog_apiserver_host: str = "0.0.0.0"
    datacatalog_apiserver_port: int = 80
    datacatalog_apiserver_json_storage_path: str = DEFAULT_JSON_FILEPATH

    class Config:
        env_file = "config.env"