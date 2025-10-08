

import uuid
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import mapped_column
from .base import BaseORMModel


class IrModel(BaseORMModel):
    __tablename__ = "ir_model"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    model = mapped_column(String, nullable=False, unique=True, index=True)
    name = mapped_column(String, nullable=False)
    info = mapped_column(Text, nullable=True)
    state = mapped_column(String, nullable=True)
    transient = mapped_column(Boolean, default=False, nullable=True)
    
  
