import logging
from typing import Annotated

from fastapi import Depends
from openg2p_fastapi_auth.beneficiary_token import BeneficiaryToken
from openg2p_fastapi_auth.models.credentials import AuthCredentials
from openg2p_fastapi_common.controller import BaseController
from openg2p_registry_models.errors import RegistryException
from openg2p_registry_models.schemas import (
    ProgramFormRequest,
    ProgramFormResponse,
    RegistryActionsResponse,
    RegistryRequest,
    RegistryResponse,
    RegistryResponseDetailResponse,
)

from ..config import Settings
from ..services import RegistryService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class RegistryController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["Registry Bene Portal - Registry"]
        self.registry_service = RegistryService.get_component()
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
            responses={200: {"model": RegistryResponseDetailResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_actions_on_registry",
            self.get_actions_on_registry,
            responses={200: {"model": RegistryActionsResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_program_form",
            self.get_program_form,
            responses={200: {"model": ProgramFormResponse}},
            methods=["POST"],
        )

    async def get_my_registries(
        self,
        registry_request: RegistryRequest,
        auth_credentials: Annotated[AuthCredentials, Depends(BeneficiaryToken())],
    ) -> RegistryResponse:
        _logger.debug("Get My Registries Request: %s", registry_request)
        try:
            if not auth_credentials:
                _logger.error("Authentication credentials are missing")
                raise RegistryException(
                    code="AUTH001", message="Authentication credentials are missing"
                )
            beneficiary_id = auth_credentials.sub
            beneficiary_id = 1
            _logger.info("Fetching registries for Beneficiary ID: %s", beneficiary_id)
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
    ) -> RegistryResponseDetailResponse:
        _logger.debug("Get Registry Request: %s", registry_request)
        try:
            registry_response: RegistryResponseDetailResponse = (
                await self.registry_service.get_registry(registry_request)
            )
            _logger.info("Registry retrieved successfully")
            _logger.debug("Get Registry Response: %s", registry_response)
            return registry_response
        except RegistryException as e:
            error_response: RegistryResponseDetailResponse = (
                await self.registry_service.construct_registry_detail_failure_response(
                    registry_request, e.code, e.message, payload_kind="detail"
                )
            )
            return error_response

    async def get_actions_on_registry(
        self,
        registry_request: RegistryRequest,
        auth_credentials: Annotated[AuthCredentials, Depends(BeneficiaryToken())],
    ) -> RegistryActionsResponse:
        registry_id = registry_request.request_body.request_payload.registry_id

        try:
            _logger.debug("Get Actions on Registry Request: %s", registry_request)

            registry_actions_response: RegistryActionsResponse = (
                await self.registry_service.get_actions_on_registry(registry_request)
            )

            _logger.debug(
                "Get Actions on Registry Response: %s", registry_actions_response
            )
            _logger.info(
                "Exiting get_actions_on_registry for Registry ID: %s - Success",
                registry_id,
            )
            return registry_actions_response

        except RegistryException as e:
            _logger.error(
                "RegistryException while fetching actions for Registry ID %s: %s",
                registry_id,
                e.message,
            )
            return await self.registry_service.construct_registry_failure_response(
                registry_request, e.code, e.message, payload_kind="actions"
            )

    async def get_program_form(
        self,
        program_form_request: ProgramFormRequest,
        auth_credentials: Annotated[AuthCredentials, Depends(BeneficiaryToken())],
    ) -> ProgramFormResponse:
        try:
            _logger.debug("Get Program Form Request: %s", program_form_request)

            program_form_response: ProgramFormResponse = (
                await self.registry_service.get_program_form(program_form_request)
            )

            _logger.debug("Get Program Form Response: %s", program_form_response)
            _logger.info("Exiting get_program_form - Success")
            return program_form_response

        except RegistryException as e:
            _logger.error(
                "RegistryException while fetching program form: %s",
                e.message,
            )
            return await self.registry_service.construct_registry_failure_response(
                program_form_request, e.code, e.message, payload_kind="actions"
            )
