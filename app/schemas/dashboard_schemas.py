from pydantic import BaseModel

class BaseORMModel(BaseModel):
    class Config:
        from_attributes = True

class tcodeGraph(BaseORMModel):
    transaction_code: str
    log_count: int

class systemIDGraph(BaseORMModel):
    sap_system_id: str
    log_count_forSystem_id: int

class criticalityDonutChart(BaseORMModel):
    criticality: str
    criticality_log_count: int

class auditClassSpagettiChart(BaseORMModel):
    audit_class: str
    audit_log_count: int

class EventCount(BaseORMModel):
    total_count: int
