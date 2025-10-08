from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PRegistyType(BaseORMModel):
    __tablename__ = "g2p_registry_type"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    registry_name = mapped_column(String, nullable=False)
    registry_unique_id = mapped_column(String, nullable=False)
    registry_creation_date = mapped_column(DateTime, nullable=False)
    registry_last_updation_date = mapped_column(DateTime, nullable=True)
    registry_details = mapped_column(Text, nullable=True)
    registry_model_name = mapped_column(String)
    domain = mapped_column(Text)
