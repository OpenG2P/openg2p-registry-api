import logging
from datetime import datetime
from typing import List

from openg2p_fastapi_common.schemas import (
    G2PResponseHeader,
    G2PResponseStatus,
)
from openg2p_fastapi_common.service import BaseService
from openg2p_registry_models.errors import RegistryErrorCodes, RegistryException
from openg2p_registry_models.models import (
    FormIOBuilder,
    G2PRegistryAction,
    G2PRegistyType,
)
from openg2p_registry_models.schemas.bene_portal_schemas import (
    ProgramFormRequest,
    ProgramFormResponse,
    ProgramFormResponseBody,
    Registry,
    RegistryAction,
    RegistryActions,
    RegistryActionsResponse,
    RegistryActionsResponseBody,
    RegistryRequest,
    RegistryResponse,
    RegistryResponseBody,
    RegistryResponseDetailResponse,
    RegistryResponseDetailResponseBody,
)
from sqlalchemy import MetaData, Table, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import Settings
from ..engine import get_engine

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


class RegistryService(BaseService):
    def __init__(self):
        self.registry_session = async_sessionmaker(
            bind=_engine.get("db_engine_registry"), expire_on_commit=False
        )

    async def get_my_registries(
        self, beneficiary_id: int, registry_request: RegistryRequest
    ) -> RegistryResponse:
        """
        Retrieve all registries where the beneficiary is enrolled.
        """
        try:
            _logger.info(f"Fetching registries for beneficiary_id: {beneficiary_id}")

            pagination = (
                registry_request.request_body.pagination_request
                if registry_request.request_body
                else None
            )

            page_size = pagination.page_size if pagination else 10
            current_page = pagination.current_page if pagination else 1
            offset = (current_page - 1) * page_size

            _logger.debug(
                f"Pagination params - page_size: {page_size}, current_page: {current_page}, offset: {offset}"
            )

            metadata = MetaData()
            registries_found: List[Registry] = []

            async with self.registry_session() as session:
                all_registries_result = await session.execute(
                    select(G2PRegistyType).order_by(
                        G2PRegistyType.registry_creation_date.desc()
                    )
                )
                all_registry_models = all_registries_result.scalars().all()

                if not all_registry_models:
                    _logger.warning("No registries found in database")
                    raise RegistryException(
                        code=RegistryErrorCodes.REGISTRY_NOT_FOUND,
                        message="No registries found",
                    )

                _logger.info(f"Found {len(all_registry_models)} total registries")
                _logger.debug(
                    f"Checking beneficiary {beneficiary_id} enrollment in each registry"
                )

                # Check each registry to see if beneficiary exists in its underlying table
                for registry_model in all_registry_models:
                    if not registry_model.registry_model_name:
                        _logger.warning(
                            f"Registry {registry_model.id} has no associated model name, skipping"
                        )
                        continue

                    try:
                        # Convert model name to table name format (e.g., "res.partner" -> "res_partner")
                        table_name = registry_model.registry_model_name.replace(
                            ".", "_"
                        )
                        _logger.debug(
                            f"Checking table {table_name} for registry {registry_model.id}"
                        )

                        # Dynamically load the beneficiary table using SQLAlchemy reflection
                        conn = await session.connection()
                        beneficiary_table = await conn.run_sync(
                            lambda sync_conn, table_name=table_name: Table(
                                table_name, metadata, autoload_with=sync_conn
                            )
                        )

                        beneficiary_result = await session.execute(
                            select(beneficiary_table).where(
                                beneficiary_table.c.id == beneficiary_id
                            )
                        )
                        records = beneficiary_result.fetchall()

                        if records:
                            registries_found.append(
                                Registry(
                                    id=registry_model.id,
                                    registry_name=registry_model.registry_name,
                                    registry_unique_id=registry_model.registry_unique_id,
                                    registry_creation_date=registry_model.registry_creation_date.date(),
                                    registry_last_updation_date=registry_model.registry_last_updation_date.date()
                                    if registry_model.registry_last_updation_date
                                    else None,
                                    registry_details=registry_model.registry_details,
                                    registry_model_name=registry_model.registry_model_name
                                    or "",
                                    domain=registry_model.domain or "",
                                )
                            )
                            _logger.debug(
                                f"Beneficiary {beneficiary_id} found in registry: {registry_model.registry_name}"
                            )

                    except Exception as table_error:
                        _logger.warning(
                            f"Could not check table {registry_model.registry_model_name} for registry {registry_model.id}: {str(table_error)}"
                        )
                        continue

                # Apply pagination to the filtered results
                total_count = len(registries_found)
                total_pages = (total_count + page_size - 1) // page_size

                paginated_registries = registries_found[offset : offset + page_size]

                _logger.info(
                    f"Found {total_count} registries for beneficiary {beneficiary_id}"
                )
                _logger.debug(
                    f"Returning page {current_page}/{total_pages} with {len(paginated_registries)} items"
                )

            return await self.construct_registry_success_response(
                registry_request, paginated_registries, total_count, total_pages
            )

        except RegistryException as re:
            _logger.error(f"RegistryException: {re.message} (code: {re.code})")
            return await self.construct_registry_failure_response(
                registry_request, re.code, re.message
            )
        except Exception as e:
            _logger.exception(f"Unexpected error while fetching registries: {str(e)}")
            return await self.construct_registry_failure_response(
                registry_request,
                RegistryErrorCodes.INTERNAL_ERROR,
                str(e),
            )

    async def get_all_registries(
        self, registry_request: RegistryRequest
    ) -> RegistryResponse:
        try:
            _logger.info("Fetching all registries")

            pagination = (
                registry_request.request_body.pagination_request
                if registry_request.request_body
                else None
            )

            page_size = pagination.page_size if pagination else 10
            current_page = pagination.current_page if pagination else 1
            offset = (current_page - 1) * page_size

            _logger.debug(
                f"Pagination params - page_size: {page_size}, current_page: {current_page}, offset: {offset}"
            )

            async with self.registry_session() as session:
                total_count_result = await session.execute(
                    select(func.count(G2PRegistyType.id))
                )
                total_count = total_count_result.scalar()
                total_pages = (total_count + page_size - 1) // page_size

                _logger.debug(
                    f"Total registries: {total_count}, total pages: {total_pages}"
                )

                registries_result = await session.execute(
                    select(G2PRegistyType)
                    .offset(offset)
                    .limit(page_size)
                    .order_by(G2PRegistyType.registry_creation_date.desc())
                )
                registry_models = registries_result.scalars().all()

                if not registry_models:
                    _logger.warning("No registries found in database")
                    raise RegistryException(
                        code=RegistryErrorCodes.REGISTRY_NOT_FOUND,
                        message="No registries found",
                    )

                _logger.info(
                    f"Retrieved {len(registry_models)} registries for page {current_page}"
                )

                registries_found: List[Registry] = []
                for registry_model in registry_models:
                    registries_found.append(
                        Registry(
                            id=registry_model.id,
                            registry_name=registry_model.registry_name,
                            registry_unique_id=registry_model.registry_unique_id,
                            registry_creation_date=registry_model.registry_creation_date.date(),
                            registry_last_updation_date=registry_model.registry_last_updation_date.date()
                            if registry_model.registry_last_updation_date
                            else None,
                            registry_details=registry_model.registry_details,
                            registry_model_name=registry_model.registry_model_name
                            or "",
                            domain=registry_model.domain or "",
                        )
                    )

            return await self.construct_registry_success_response(
                registry_request, registries_found, total_count, total_pages
            )

        except RegistryException as re:
            _logger.error(f"RegistryException: {re.message} (code: {re.code})")
            return await self.construct_registry_failure_response(
                registry_request, re.code, re.message
            )
        except Exception as e:
            _logger.exception(
                f"Unexpected error while fetching all registries: {str(e)}"
            )
            return await self.construct_registry_failure_response(
                registry_request,
                RegistryErrorCodes.INTERNAL_ERROR,
                str(e),
            )

    async def get_registry(
        self, registry_request: RegistryRequest
    ) -> RegistryResponseDetailResponse:
        """
        Retrieve detailed information for a specific registry by its unique ID.
        """
        try:
            registry_id = (
                registry_request.request_body.request_payload.registry_id
                if registry_request.request_body
                and registry_request.request_body.request_payload
                else None
            )

            if not registry_id:
                _logger.warning("Registry request missing registry_id")
                raise RegistryException(
                    code=RegistryErrorCodes.INVALID_REQUEST,
                    message="registry_id is required",
                )

            _logger.info(f"Fetching registry details for registry_id: {registry_id}")

            async with self.registry_session() as session:
                registry_result = await session.execute(
                    select(G2PRegistyType).where(
                        G2PRegistyType.registry_unique_id == registry_id
                    )
                )
                registry_model = registry_result.scalar_one_or_none()

                if not registry_model:
                    _logger.warning(
                        f"Registry not found for registry_id: {registry_id}"
                    )
                    raise RegistryException(
                        code=RegistryErrorCodes.REGISTRY_NOT_FOUND,
                        message=f"Registry not found for registry_id: {registry_id}",
                    )

                _logger.info(f"Found registry: {registry_model.registry_name}")

                registry = Registry(
                    id=registry_model.id,
                    registry_name=registry_model.registry_name,
                    registry_unique_id=registry_model.registry_unique_id,
                    registry_creation_date=registry_model.registry_creation_date.date(),
                    registry_last_updation_date=registry_model.registry_last_updation_date.date()
                    if registry_model.registry_last_updation_date
                    else None,
                    registry_details=registry_model.registry_details,
                    registry_model_name=registry_model.registry_model_name or "",
                    domain=registry_model.domain or "",
                )

            return await self.construct_registry_detail_success_response(
                registry_request, registry
            )

        except RegistryException as re:
            _logger.error(f"RegistryException: {re.message} (code: {re.code})")
            return await self.construct_registry_failure_response(
                registry_request, re.code, re.message, payload_kind="detail"
            )
        except Exception as e:
            _logger.exception(f"Unexpected error while fetching registry: {str(e)}")
            return await self.construct_registry_failure_response(
                registry_request,
                RegistryErrorCodes.INTERNAL_ERROR,
                str(e),
                payload_kind="detail",
            )

    async def get_actions_on_registry(
        self, registry_request: RegistryRequest
    ) -> RegistryActionsResponse:
        """
        Retrieve all configured actions for a specific registry.
        """
        try:
            registry_unique_id = (
                registry_request.request_body.request_payload.registry_id
                if registry_request.request_body
                and registry_request.request_body.request_payload
                else None
            )

            if not registry_unique_id:
                _logger.warning("Actions request missing registry_id")
                raise RegistryException(
                    code=RegistryErrorCodes.INVALID_REQUEST,
                    message="registry_id is required",
                )

            _logger.info(f"Fetching actions for registry_id: {registry_unique_id}")

            pagination = (
                registry_request.request_body.pagination_request
                if registry_request.request_body
                else None
            )

            page_size = pagination.page_size if pagination else 10
            current_page = pagination.current_page if pagination else 1
            offset = (current_page - 1) * page_size

            _logger.debug(
                f"Pagination params - page_size: {page_size}, current_page: {current_page}, offset: {offset}"
            )

            async with self.registry_session() as session:
                registry_result = await session.execute(
                    select(G2PRegistyType).where(
                        G2PRegistyType.registry_unique_id == registry_unique_id
                    )
                )
                registry_model = registry_result.scalar_one_or_none()

                if not registry_model:
                    _logger.warning(
                        f"Registry not found for registry_id: {registry_unique_id}"
                    )
                    raise RegistryException(
                        code=RegistryErrorCodes.REGISTRY_NOT_FOUND,
                        message=f"Registry not found for registry_id: {registry_unique_id}",
                    )

                _logger.debug(
                    f"Found registry: {registry_model.registry_name}, fetching associated actions"
                )

                # Get total count of actions
                total_count_result = await session.execute(
                    select(func.count(G2PRegistryAction.id)).where(
                        G2PRegistryAction.registry_type_id == registry_model.id
                    )
                )
                total_count = total_count_result.scalar()
                total_pages = (total_count + page_size - 1) // page_size

                _logger.debug(
                    f"Total actions: {total_count}, total pages: {total_pages}"
                )

                # Get paginated actions
                actions_result = await session.execute(
                    select(G2PRegistryAction)
                    .where(G2PRegistryAction.registry_type_id == registry_model.id)
                    .offset(offset)
                    .limit(page_size)
                )
                action_models = actions_result.scalars().all()

                _logger.info(
                    f"Found {len(action_models)} actions for registry {registry_model.registry_name} (page {current_page}/{total_pages})"
                )

                actions_payload = [
                    RegistryAction(
                        id=action.id,
                        registry_id=registry_model.id,
                        action_name=action.action_name,
                        form_uuid=action.formio_uuid,
                        form_schema=action.formio_schema,
                    )
                    for action in action_models
                ]

                actions_wrapper = RegistryActions(
                    registry_id=registry_model.id, registry_actions=actions_payload
                )

            pagination_response = None
            if total_count > 0 or total_pages > 0:
                pagination_response = {
                    "number_of_items": total_count,
                    "number_of_pages": total_pages,
                }

            return RegistryActionsResponse(
                response_header=G2PResponseHeader(
                    request_id=registry_request.request_header.request_id,
                    response_status=G2PResponseStatus.SUCCESS,
                    response_timestamp=datetime.utcnow(),
                ),
                response_body=RegistryActionsResponseBody(
                    response_payload=actions_wrapper,
                    pagination_response=pagination_response,
                ),
            )
        except RegistryException as re:
            _logger.error(
                f"RegistryException while fetching actions: {re.message} (code: {re.code})"
            )
            return await self.construct_registry_failure_response(
                registry_request, re.code, re.message, payload_kind="actions"
            )
        except Exception as e:
            _logger.exception(
                f"Unexpected error while fetching registry actions: {str(e)}"
            )
            return await self.construct_registry_failure_response(
                registry_request,
                RegistryErrorCodes.INTERNAL_ERROR,
                str(e),
                payload_kind="actions",
            )

    async def get_program_form(
        self, program_form_request: ProgramFormRequest
    ) -> ProgramFormResponse:
        """
        Retrieve program form schema by formio_uuid using FormIOBuilder.
        """
        try:
            formio_uuid = (
                program_form_request.request_body.request_payload.formio_uuid
                if program_form_request.request_body
                and program_form_request.request_body.request_payload
                else None
            )

            if not formio_uuid:
                _logger.warning("Program form request missing formio_uuid")
                raise RegistryException(
                    code=RegistryErrorCodes.INVALID_REQUEST,
                    message="formio_uuid is required",
                )

            _logger.info(f"Fetching program form for formio_uuid: {formio_uuid}")

            async with self.registry_session() as session:
                result = await session.execute(
                    select(FormIOBuilder).where(FormIOBuilder.uuid == formio_uuid)
                )
                form_model = result.scalar_one_or_none()

                if not form_model:
                    _logger.warning(
                        f"Program form not found for formio_uuid: {formio_uuid}"
                    )
                    raise RegistryException(
                        code=RegistryErrorCodes.REGISTRY_NOT_FOUND,
                        message=f"Program form not found for formio_uuid: {formio_uuid}",
                    )

                wrapper = {
                    "form_id": form_model.id,
                    "form_schema": form_model.schema,
                }

            return ProgramFormResponse(
                response_header=G2PResponseHeader(
                    request_id=program_form_request.request_header.request_id,
                    response_status=G2PResponseStatus.SUCCESS,
                    response_timestamp=datetime.utcnow(),
                ),
                response_body=ProgramFormResponseBody(response_payload=wrapper),
            )

        except RegistryException as re:
            _logger.error(
                f"RegistryException while fetching program form: {re.message} (code: {re.code})"
            )
            return await self.construct_registry_failure_response(
                program_form_request, re.code, re.message, payload_kind="program_form"
            )
        except Exception as e:
            _logger.exception(f"Unexpected error while fetching program form: {str(e)}")
            return await self.construct_registry_failure_response(
                program_form_request,
                RegistryErrorCodes.INTERNAL_ERROR,
                str(e),
                payload_kind="program_form",
            )

    async def construct_registry_failure_response(
        self,
        registry_request,
        error_code: str,
        error_message: str,
        payload_kind: str = "list",
    ):
        """
        Construct error responses for different payload types.
        """
        response_header = G2PResponseHeader(
            request_id=registry_request.request_header.request_id,
            response_status=G2PResponseStatus.ERROR,
            response_error_code=error_code,
            response_error_message=error_message,
            response_timestamp=datetime.utcnow(),
        )

        if payload_kind == "detail":
            return RegistryResponseDetailResponse(
                response_header=response_header,
                response_body=RegistryResponseDetailResponseBody(response_payload=None),
            )
        if payload_kind == "actions":
            return RegistryActionsResponse(
                response_header=response_header,
                response_body=RegistryActionsResponseBody(
                    response_payload=RegistryActions(
                        registry_id=0,
                        registry_actions=[],
                    )
                ),
            )

        if payload_kind == "program_form":
            return ProgramFormResponse(
                response_header=response_header,
                response_body=ProgramFormResponseBody(response_payload={}),
            )

        response_body = RegistryResponseBody(response_payload=[])
        return RegistryResponse(
            response_header=response_header,
            response_body=response_body,
        )

    async def construct_registry_success_response(
        self,
        registry_request: RegistryRequest,
        registries: List[Registry],
        total_count: int = 0,
        total_pages: int = 0,
    ) -> RegistryResponse:
        """
        Construct successful registry list response with optional pagination metadata.
        """
        pagination_response = None
        if total_count > 0 or total_pages > 0:
            pagination_response = {
                "number_of_items": total_count,
                "number_of_pages": total_pages,
            }

        return RegistryResponse(
            response_header=G2PResponseHeader(
                request_id=registry_request.request_header.request_id,
                response_status=G2PResponseStatus.SUCCESS,
                response_timestamp=datetime.utcnow(),
            ),
            response_body=RegistryResponseBody(
                response_payload=registries,
                pagination_response=pagination_response,
            ),
        )

    async def construct_registry_detail_success_response(
        self,
        registry_request: RegistryRequest,
        registry: Registry,
    ) -> RegistryResponseDetailResponse:
        """
        Construct successful registry detail response for a single registry.
        """
        return RegistryResponseDetailResponse(
            response_header=G2PResponseHeader(
                request_id=registry_request.request_header.request_id,
                response_status=G2PResponseStatus.SUCCESS,
                response_timestamp=datetime.utcnow(),
            ),
            response_body=RegistryResponseDetailResponseBody(response_payload=registry),
        )
