from pydantic import BaseModel
from datetime import datetime

class LogEntryBase(BaseModel):
    sap_system_id: str
    app_server_instance: str
    message_identifier: str
    syslog_msg_group: str
    sub_name: str
    date: str
    time: str
    operating_system_number: str
    work_process_number: str
    sap_process :str
    client: str
    file_number: str
    short_terminal_name :str
    user: str
    transaction_code: str
    program: str
    long_terminal_name: str
    last_address_routed_no_of_variables: str
    first_variable_value: str
    second_variable_value: str
    third_variable_value: str
    audit_log_msg_text: str
    # long_version_of_event: str
    audit_class: str
    message_severity: str
    criticality: str
    other_variable_values: str
    

    class Config:
        orm_mode = True

class LogEntryResponse(LogEntryBase):
    id: int
