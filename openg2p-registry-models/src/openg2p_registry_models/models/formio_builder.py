from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseORMModel

class FormIOBuilder(BaseORMModel):
    __tablename__ = "formio_builder"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String())
    schema: Mapped[str] = mapped_column(String())

