from typing import List, cast
from fastapi import APIRouter, Depends, HTTPException, Form,Query
from sqlalchemy.orm import Session
from datetime import datetime,date

from app.models.database import get_db
from app.models.log import LogEntry
from app.schemas.dashboard_schemas import tcodeGraph, systemIDGraph, criticalityDonutChart, \
    auditClassSpagettiChart, EventCount  # You need to define this schema
from sqlalchemy import and_, func, Date

router = APIRouter()

@router.get("/dashboard/tcode_onDate/", response_model=List[tcodeGraph])
async def filter_dashboard_by_t_code(
        start_date: date = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: date = Query(None, description="End date (YYYY-MM-DD)"),
        db: Session = Depends(get_db)
):
    try:
        start_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_str = end_date.strftime("%Y-%m-%d") if end_date else None
        if start_str and end_str:
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="Start date must be before end date")

        query = db.query(LogEntry.transaction_code, func.count().label("log_count"))
        if start_str:
            query = query.filter(LogEntry.date >= start_str)
        if end_str:
            query = query.filter(LogEntry.date <= end_str)
        query = query.filter(
            and_(
                LogEntry.transaction_code.isnot(None),
                func.length(func.trim(LogEntry.transaction_code)) > 0
            )
        )
        query = query.group_by(LogEntry.transaction_code).order_by(func.count().desc()).limit(10)

        results = query.all()

        return [{"transaction_code": t_code, "log_count": count} for t_code, count in results]

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")



@router.get("/dashboard/s_id_onDate/", response_model=List[systemIDGraph])
async def filter_dashboard_by_systemId(
        start_date: date = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: date = Query(None, description="End date (YYYY-MM-DD)"),
        db: Session = Depends(get_db)
):
    try:
        start_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_str = end_date.strftime("%Y-%m-%d") if end_date else None
        if start_str and end_str:
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="Start date must be before end date")
        query = db.query(LogEntry.sap_system_id, func.count().label("log_count_forSystem_id"))

        if start_str:
            query = query.filter(LogEntry.date >= start_str)
        if end_str:
            query = query.filter(LogEntry.date <= end_str)
        query = query.group_by(LogEntry.sap_system_id).order_by(func.count().desc()).limit(10)


        results = query.all()

        return [{"sap_system_id": sap_system_id, "log_count_forSystem_id": count} for sap_system_id, count in results]

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")



@router.get("/dashboard/criticality_onDate/", response_model=List[criticalityDonutChart])
async def filter_dashboard_by_criticality(
        start_date: date = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: date = Query(None, description="End date (YYYY-MM-DD)"),
        db: Session = Depends(get_db)
):
    try:
        start_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_str = end_date.strftime("%Y-%m-%d") if end_date else None
        if start_str and end_str and start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        query = db.query(LogEntry.criticality, func.count().label("criticality_log_count"))

        if start_str:
            query = query.filter(LogEntry.date >= start_str)
        if end_str:
            query = query.filter(LogEntry.date <= end_str)
        query = query.group_by(LogEntry.criticality).order_by(func.count().desc())


        results = query.all()

        return [{"criticality": criticality, "criticality_log_count": count} for criticality, count in results]

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")




@router.get("/dashboard/auditclasses_onDate/", response_model=List[auditClassSpagettiChart])
async def filter_dashboard_by_auditclasses(
        start_date: date = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: date = Query(None, description="End date (YYYY-MM-DD)"),
        db: Session = Depends(get_db)
):
    try:
        start_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_str = end_date.strftime("%Y-%m-%d") if end_date else None
        if start_str and end_str and start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        query = db.query(LogEntry.audit_class, func.count().label("audit_log_count"))

        if start_str:
            query = query.filter(LogEntry.date >= start_str)
        if end_str:
            query = query.filter(LogEntry.date <= end_str)

        query = query.group_by(LogEntry.audit_class).order_by(func.count().desc())


        results = query.all()

        return [{"audit_class": audit_class, "audit_log_count": count} for audit_class, count in results]

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.get("/home/totaleventCount/", response_model=EventCount)
async def filter_dashboard_by_t_code(
        start_date: date = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: date = Query(None, description="End date (YYYY-MM-DD)"),
        db: Session = Depends(get_db)
):
    try:
        start_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_str = end_date.strftime("%Y-%m-%d") if end_date else None
        if start_str and end_str:
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="Start date must be before end date")

        query = db.query(func.count().label("total_count"))
        if start_str:
            query = query.filter(LogEntry.date >= start_str)
        if end_str:
            query = query.filter(LogEntry.date <= end_str)

        total_count = query.scalar()
        return {"total_count": total_count}

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")



