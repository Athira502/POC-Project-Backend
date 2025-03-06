
from sqlalchemy import Column, String, Integer, DateTime
from app.models.database import Base
class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    sap_system_id = Column(String, index=True)
    app_server_instance = Column(String)
    message_identifier = Column(String)
    syslog_msg_group = Column(String,nullable=True)
    sub_name = Column(String,nullable=True)
    date = Column(String)
    time = Column(String)
    operating_system_number = Column(String,nullable=True)
    work_process_number = Column(String,nullable=True)
    sap_process = Column(String,nullable=True)
    client = Column(String,nullable=True)
    file_number = Column(String,nullable=True)
    short_terminal_name = Column(String,nullable=True)
    user = Column(String,nullable=True)
    transaction_code = Column(String,nullable=True)
    program = Column(String,nullable=True)
    long_terminal_name=Column(String,nullable=True)
    last_address_routed_no_of_variables= Column(String,nullable=True)
    first_variable_value = Column(String,nullable=True)
    second_variable_value = Column(String,nullable=True)
    third_variable_value = Column(String,nullable=True)
    audit_log_msg_text = Column(String,nullable=True)
    audit_class = Column(String,nullable=True)
    message_severity = Column(String,nullable=True)
    criticality =Column(String,nullable=True)
    other_variable_values = Column(String,nullable=True)
    
    
