from sqlalchemy import Integer, String, JSON, ForeignKey
from sqlalchemy.orm import mapped_column
from .base import BaseORMModel


class G2PRegistryAction(BaseORMModel):
    __tablename__ = "g2p_registry_action"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_name = mapped_column(String, nullable=False)
    formio_schema = mapped_column(JSON, nullable=True)
    action_submission_url = mapped_column(String, nullable=True)

    registry_model_id = mapped_column(
        Integer,
        ForeignKey("ir_model.id"),
        nullable=True,
    )
    form_builder_id = mapped_column(
        Integer,
        ForeignKey("formio_builder.id"),
        nullable=True,
    )
