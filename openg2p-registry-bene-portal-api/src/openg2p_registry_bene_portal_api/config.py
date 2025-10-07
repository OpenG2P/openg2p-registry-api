from openg2p_fastapi_common.config import Settings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(Settings):
    model_config = SettingsConfigDict(
        env_prefix="registry_bene_portal_api_", env_file=".env", extra="allow"
    )

    openapi_title: str = "OpenG2P Registry Bene Portal API"
    openapi_description: str = """
        FastAPI Service for OpenG2P Registry Bene Portal API
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    db_username_registry: str = "postgres"
    db_password_registry: str = "password"
    db_hostname_registry: str = "localhost"
    db_port_registry: int = 5432
    db_dbname_registry: str = "sr_db"
