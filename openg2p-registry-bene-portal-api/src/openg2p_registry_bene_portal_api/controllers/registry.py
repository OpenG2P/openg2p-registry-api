import logging
from typing import Annotated

from fastapi import Depends
from openg2p_fastapi_auth.beneficiary_token import BeneficiaryToken
from openg2p_fastapi_auth.models.credentials import AuthCredentials
from openg2p_fastapi_common.controller import BaseController
from openg2p_registry_models.errors import RegistryException
from openg2p_registry_models.schemas.bene_portal_schemas import (
    RegistryRequest,
    RegistryResponse,
)
from openg2p_registry_models.schemas import (
    RegistryResponseDetailResponse as RegistryDetailResponse,
)

from ..config import Settings
from ..services import RegistryService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class RegistryController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["Registry Bene Portal - Registry"]
        self.registry_service = RegistryService()
        self.router.prefix = "/registry"

        self.router.add_api_route(
            "/get_my_registries",
            self.get_my_registries,
            responses={200: {"model": RegistryResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_all_registries",
            self.get_all_registries,
            responses={200: {"model": RegistryResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_registry",
            self.get_registry,
            responses={200: {"model": RegistryDetailResponse}},
            methods=["POST"],
        )

    async def get_my_registries(
        self,
        registry_request: RegistryRequest,
        auth_credentials: Annotated[AuthCredentials, Depends(BeneficiaryToken())],
    ) -> RegistryResponse:
        _logger.debug("Get My Registries Request: %s", registry_request)
        try:
            beneficiary_id = auth_credentials.sub
            
            registry_response: RegistryResponse = (
                await self.registry_service.get_my_registries(
                    beneficiary_id, registry_request
                )
            )
            _logger.info("Registries retrieved successfully")
            _logger.debug("Get My Registries Response: %s", registry_response)
            return registry_response
        except RegistryException as e:
            error_response: RegistryResponse = (
                await self.registry_service.construct_registry_failure_response(
                    registry_request, e.code, e.message
                )
            )
            return error_response

    async def get_all_registries(
        self,
        registry_request: RegistryRequest,
        auth_credentials: Annotated[AuthCredentials, Depends(BeneficiaryToken())],
    ) -> RegistryResponse:
        _logger.debug("Get All Registries Request: %s", registry_request)
        try:
            registry_response: RegistryResponse = (
                await self.registry_service.get_all_registries(registry_request)
            )
            _logger.info("All registries retrieved successfully")
            _logger.debug("Get All Registries Response: %s", registry_response)
            return registry_response
        except RegistryException as e:
            error_response: RegistryResponse = (
                await self.registry_service.construct_registry_failure_response(
                    registry_request, e.code, e.message
                )
            )
            return error_response

    async def get_registry(
        self,
        registry_request: RegistryRequest,
        auth_credentials: Annotated[AuthCredentials, Depends(BeneficiaryToken())],
    ) -> RegistryDetailResponse:
        _logger.debug("Get Registry Request: %s", registry_request)
        try:
            registry_response: RegistryDetailResponse = (
                await self.registry_service.get_registry(registry_request)
            )
            _logger.info("Registry retrieved successfully")
            _logger.debug("Get Registry Response: %s", registry_response)
            return registry_response
        except RegistryException as e:
            error_response: RegistryDetailResponse = (
                await self.registry_service.construct_registry_detail_failure_response(
                    registry_request, e.code, e.message
                )
            )
            return error_response
