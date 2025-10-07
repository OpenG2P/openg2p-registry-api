import logging
from datetime import date, datetime
from typing import List

from openg2p_fastapi_common.schemas import (
    G2PResponseHeader,
    G2PResponseStatus,
)
from openg2p_fastapi_common.service import BaseService
from openg2p_registry_models.errors import RegistryErrorCodes, RegistryException
from openg2p_registry_models.models import G2PRegistryModel, IrModel
from openg2p_registry_models.schemas.bene_portal_schemas import (
    Registry,
    RegistryRequest,
    RegistryResponse,
    RegistryResponseBody,
)
from sqlalchemy import MetaData, Table, select
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
        try:
            metadata = MetaData()
            registry_id = (
                registry_request.request_body.request_payload.registry_id
                if registry_request.request_body
                and registry_request.request_body.request_payload
                else None
            )

            if not registry_id:
                raise RegistryException(
                    code=RegistryErrorCodes.INVALID_REQUEST,
                    message="registry_id missing in request payload",
                )

            registries_found: List[Registry] = []

            async with self.registry_session() as session:
                registry_result = await session.execute(
                    select(G2PRegistryModel).where(
                        G2PRegistryModel.registry_unique_id == registry_id
                    )
                )
                registry_models = registry_result.scalars().all()

                if not registry_models:
                    raise RegistryException(
                        code=RegistryErrorCodes.REGISTRY_NOT_FOUND,
                        message=f"No registries found for registry_id: {registry_id}",
                    )

                _logger.info(
                    f"Found {len(registry_models)} registry configuration(s) for registry_id: {registry_id}"
                )

                for registry_model in registry_models:
                    if not registry_model.registry_model:
                        _logger.warning(
                            f"Registry {registry_model.id} has no associated model"
                        )
                        continue

                    ir_model_result = await session.execute(
                        select(IrModel).where(
                            IrModel.id == registry_model.registry_model
                        )
                    )
                    ir_model_record = ir_model_result.scalar_one_or_none()

                    if not ir_model_record or not ir_model_record.model:
                        _logger.warning(
                            f"Registry {registry_model.id} has invalid ir_model mapping"
                        )
                        continue

                    table_name = ir_model_record.model.replace(".", "_")
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
                                registry_last_updation_date=registry_model.registry_last_updation_date.date(),
                                registry_details=registry_model.registry_details,
                            )
                        )

            return RegistryResponse(
                response_header=G2PResponseHeader(
                    request_id=registry_request.request_header.request_id,
                    response_status=G2PResponseStatus.SUCCESS,
                    response_timestamp=datetime.utcnow(),
                ),
                response_body=RegistryResponseBody(response_payload=registries_found),
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

    async def construct_registry_failure_response(
        self,
        registry_request,
        error_code: str,
        error_message: str,
    ) -> RegistryResponse:
        response_header = G2PResponseHeader(
            request_id=registry_request.request_header.request_id,
            response_status=G2PResponseStatus.ERROR,
            response_timestamp=datetime.utcnow(),
        )
        response_body = RegistryResponseBody(
            response_payload=[
                {
                    "id": 0,
                    "registry_name": "Error",
                    "registry_unique_id": error_code,
                    "registry_creation_date": date.today(),
                    "registry_details": f"Error Code: {error_code}, Message: {error_message}",
                }
            ]
        )

        return RegistryResponse(
            response_header=response_header,
            response_body=response_body,
        )
