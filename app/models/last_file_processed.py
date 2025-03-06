from sqlalchemy import Column, String, Integer, DateTime
from app.models.database import Base
from sqlalchemy.sql import func


class lastfileEntry(Base):
    __tablename__ = "last_file_processed"

    id = Column(Integer, primary_key=True, index=True)
    sap_system_id = Column(String)
    app_server_instance = Column(String)
    file_name =Column(String)
    file_path=Column(String)
    date_processed= Column(DateTime, default=func.now())

