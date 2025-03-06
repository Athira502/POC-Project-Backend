
from sqlalchemy import Column, String, Integer, DateTime
from app.models.database import Base



class filepathEntry(Base):
    __tablename__ = "file_path"

    id = Column(Integer, primary_key=True, index=True)
    sap_system_id = Column(String)
    # , index = True, default = "S4H"
    app_server_instance = Column(String)
    # , default = "vhcals4hci_S4H_00"
    file_path=Column(String)
    delimiter=Column(String)