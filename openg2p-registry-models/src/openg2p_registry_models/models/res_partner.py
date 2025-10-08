from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class Gender(Enum):
    Male = "Male"
    Female = "Female"


class ResPartner(BaseORMModel):
    __tablename__ = "res_partner"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String, nullable=False)
    given_name = mapped_column(String, nullable=False)
    family_name = mapped_column(String, nullable=False)
    addl_name = mapped_column(String)
    gender = mapped_column(SqlEnum(Gender))
    address = mapped_column(Text)
    create_date = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    write_date = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
