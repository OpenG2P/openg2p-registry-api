from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PRegistryAction(BaseORMModel):
    __tablename__ = "g2p_registry_action"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_name = mapped_column(String, nullable=False)
    registry_type_id = mapped_column(
        Integer, ForeignKey("g2p_registry_type.id"), nullable=False
    )
    formio_uuid = mapped_column(String)
    formio_schema = mapped_column(Text)
    action_submission_url = mapped_column(String)
