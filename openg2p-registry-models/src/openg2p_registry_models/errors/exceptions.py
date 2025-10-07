from typing import Optional

from .codes import RegistryErrorCodes


class RegistryException(Exception):
    def __init__(
        self,
        code: RegistryErrorCodes,
        payload: Optional[object] = None,
        message: Optional[str] = None,
    ):
        self.code: RegistryErrorCodes = code
        self.message: Optional[str] = message
        self.payload: object = payload
        super().__init__(code, self.message)
