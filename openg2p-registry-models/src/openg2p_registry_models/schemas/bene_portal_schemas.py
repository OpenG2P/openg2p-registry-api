from datetime import date
from typing import List, Optional

from openg2p_fastapi_common.schemas import (
    G2PPaginationRequest,
    G2PRequest,
    G2PRequestBody,
    G2PRequestHeader,
    G2PResponse,
    G2PResponseBody,
)
from pydantic import BaseModel


class Registry(BaseModel):
    id: int
    registry_name: str
    registry_unique_id: str
    registry_creation_date: date
    registry_last_updation_date: Optional[date] = None
    registry_details: str
    registry_model_name: str
    domain: str


class RegistryAction(BaseModel):
    id: int
    registry_id: int
    action_name: str
    form_uuid: str
    form_schema: str


class RegistryActions(BaseModel):
    registry_id: int
    registry_actions: List[RegistryAction]


class RegistryRequestPayload(BaseModel):
    registry_id: str | None = None
    application_url: str | None = None


class RegistryRequestBody(G2PRequestBody):
    pagination_request: G2PPaginationRequest | None = None
    request_payload: RegistryRequestPayload | None = None


class RegistryRequest(G2PRequest):
    request_header: G2PRequestHeader
    request_body: RegistryRequestBody


class RegistryResponseBody(G2PResponseBody):
    response_payload: List[Registry]


class RegistryResponse(G2PResponse):
    response_body: RegistryResponseBody


class RegistryResponseDetailResponseBody(G2PResponseBody):
    response_payload: Optional[Registry] = None


class RegistryResponseDetailResponse(G2PResponse):
    response_body: RegistryResponseDetailResponseBody


class RegistryActionsResponseBody(G2PResponseBody):
    response_payload: RegistryActions


class RegistryActionsResponse(G2PResponse):
    response_body: RegistryActionsResponseBody


class ProgramFormRequestPayload(BaseModel):
    formio_id: str


class ProgramFormRequestBody(G2PRequestBody):
    request_payload: ProgramFormRequestPayload


class ProgramFormRequest(G2PRequest):
    request_header: G2PRequestHeader
    request_body: ProgramFormRequestBody


class ProgramFormResponseBody(G2PResponseBody):
    response_payload: dict


class ProgramFormResponse(G2PResponse):
    response_body: ProgramFormResponseBody
