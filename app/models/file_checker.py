from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from app.models.database import Base

class FilecheckerEntry(Base):
    __tablename__ = "file_checker"
    file_id = Column(Integer, primary_key=True, index=True)
    last_file_processed = Column(String, nullable=False)
    sap_system_id=Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    date = Column(DateTime, default=func.now())


