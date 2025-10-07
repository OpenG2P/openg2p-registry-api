import logging

from sqlalchemy.ext.asyncio import create_async_engine

from .config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


def construct_db_datasource(
    db_driver, db_username, db_password, db_hostname, db_port, db_dbname
) -> str:
    datasource = ""
    if db_driver:
        datasource += f"{db_driver}://"
    if db_username:
        datasource += f"{db_username}:{db_password}@"
    if db_hostname:
        datasource += db_hostname
    if db_port:
        datasource += f":{db_port}"
    if db_dbname:
        datasource += f"/{db_dbname}"

    _logger.info(f"Constructed Datasource: {datasource}")

    return datasource


def get_engine():
    engines = {}

    # Registry Database
    if hasattr(_config, "db_username_registry"):
        db_datasource_pbms = construct_db_datasource(
            _config.db_driver,
            _config.db_username_registry,
            _config.db_password_registry,
            _config.db_hostname_registry,
            _config.db_port_registry,
            _config.db_dbname_registry,
        )
        engines["db_engine_registry"] = create_async_engine(db_datasource_pbms)

    return engines
