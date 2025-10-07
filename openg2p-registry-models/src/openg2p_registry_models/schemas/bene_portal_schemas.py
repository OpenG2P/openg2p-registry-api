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


class RegistryAction(BaseModel):
    id: int
    registry_id: int
    action_name: str
    form_schema: str


class RegistryActions(BaseModel):
    registry_id: int
    registry_actions: List[RegistryAction]


# Registry Request


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


class RegistryResponseDetailResponseBody(G2PResponseBody):
    response_payload: Optional[Registry] = None


class RegistryResponse(G2PResponse):
    response_body: RegistryResponseBody


class RegistryResponseDetailResponse(G2PResponse):
    response_body: RegistryResponseDetailResponseBody


class RegistryActionsResponseBody(G2PResponseBody):
    response_payload: RegistryActions


class RegistryActionsResponse(G2PResponse):
    response_body: RegistryActionsResponseBody
