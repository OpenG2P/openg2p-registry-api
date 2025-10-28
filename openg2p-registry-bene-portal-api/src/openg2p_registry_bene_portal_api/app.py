# ruff: noqa: E402
import logging

from openg2p_fastapi_common.app import Initializer as BaseInitializer

from .config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()
