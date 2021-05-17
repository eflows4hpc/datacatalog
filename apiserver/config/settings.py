from pydantic import BaseSettings

DEFAULT_JSON_FILEPATH: str = "./app/data"

## Additional Settings can be made available by adding them as properties to this class
# At launch they will be read from environment variables (case-INsensitive)

class ApiserverSettings(BaseSettings):
    json_storage_path: str = DEFAULT_JSON_FILEPATH

    class Config:
        env_prefix: str = "datacatalog_apiserver_"
        env_file: str = "config.env"