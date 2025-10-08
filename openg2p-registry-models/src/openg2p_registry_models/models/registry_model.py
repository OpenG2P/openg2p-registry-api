# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import uuid
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import mapped_column,relationship
from .base import BaseORMModel


class G2PRegistryModel(BaseORMModel):
    __tablename__ = "g2p_registry_model"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    registry_name = mapped_column(String, nullable=False)
    registry_unique_id = mapped_column(String,nullable=False)
    registry_creation_date = mapped_column(DateTime,nullable=False)
    registry_last_updation_date = mapped_column(DateTime,nullable=True)
    registry_details = mapped_column(Text, nullable=True)

    registry_model = mapped_column(
        Integer, ForeignKey("ir_model.id"), nullable=True
    )
