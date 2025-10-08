
from sqlalchemy import  Integer
from sqlalchemy.orm import mapped_column
from .base import BaseORMModel


class ResPartner(BaseORMModel):
    __tablename__ = "res_partner"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    # if need more column add here 
    
  
