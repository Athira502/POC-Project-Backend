import os
from typing import List, Dict
from fastapi.responses import Response
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Form,Query,Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from datetime import datetime,date

from app.models.last_file_processed import lastfileEntry
from app.schemas.log_schema import LogEntryResponse, LogEntryBase, FileCheckResponse
from app.schemas.log_schema import LogEntryResponse

from app.services.log_service import parse_and_store_logs
from app.models.database import get_db
from app.models.log import LogEntry
from app.models.file_checker import FilecheckerEntry
from app.models.file_path import filepathEntry

router = APIRouter()

@router.post("/process-folder/")
async def process_folder(folder: str = Form(...), db: Session = Depends(get_db)):
    try:
        file_path_entry = db.query(filepathEntry).filter(filepathEntry.file_path.like(f"%{folder}%")).first()
        if not file_path_entry:
            raise HTTPException(status_code=400, detail="Invalid folder name")
        folder_path = file_path_entry.file_path
        sap_system_id=file_path_entry.sap_system_id

        def extract_timestamp(file_name: str):
            try:
                return datetime.strptime(file_name[:14], "%Y%m%d%H%M%S")
            except ValueError:
                return None
        files = [
            (os.path.join(folder_path, f), extract_timestamp(f))
            for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and extract_timestamp(f) is not None
        ]
        sorted_files = sorted(files, key=lambda x: x[1])
        last_processed_file = (
            db.query(lastfileEntry)
            .filter(
                lastfileEntry.sap_system_id == file_path_entry.sap_system_id,
                lastfileEntry.app_server_instance == file_path_entry.app_server_instance
            )
            .first()
        )
        last_processed_time = extract_timestamp(last_processed_file.file_name) if last_processed_file else None

        file_to_process = None
        for file in sorted_files:
            file_time = file[1]
            if last_processed_time is None or file_time > last_processed_time:
                file_to_process = file
                break

        if not file_to_process:
            return JSONResponse(status_code=200, content={"message": "No new files to process."})

        file_path, file_timestamp = file_to_process
        processed_count = 0
        errors = []

        try:
            success = parse_and_store_logs(
                file_path=file_path,
                db=db,
                sap_system_id=file_path_entry.sap_system_id,
                app_server_instance=file_path_entry.app_server_instance,
                delimiter=file_path_entry.delimiter,
                file_checker_id=None
            )

            if success:
                processed_count = 1

                existing_entry = (
                    db.query(lastfileEntry)
                    .filter(
                        lastfileEntry.sap_system_id == file_path_entry.sap_system_id,
                        lastfileEntry.app_server_instance == file_path_entry.app_server_instance
                    )
                    .first()
                )

                if existing_entry:
                    existing_entry.file_name = os.path.basename(file_path)
                    existing_entry.file_path = folder_path
                    existing_entry.date_processed = datetime.now()
                else:
                    new_entry = lastfileEntry(
                        sap_system_id=file_path_entry.sap_system_id,
                        app_server_instance=file_path_entry.app_server_instance,
                        file_name=os.path.basename(file_path),
                        file_path=folder_path,
                        date_processed=datetime.now()
                    )
                    db.add(new_entry)

                file_checker_entry = FilecheckerEntry(
                    last_file_processed=os.path.basename(file_path),
                    file_path=folder_path,
                    sap_system_id=sap_system_id,
                    date=datetime.now(),
                )
                db.add(file_checker_entry)
                db.commit()
            else:
                errors.append(f"Failed to parse: {os.path.basename(file_path)}")
                db.rollback()

        except Exception as e:
            db.rollback()
            errors.append(f"Error processing {os.path.basename(file_path)}: {str(e)}")
            raise
        finally:
            db.close()

        return JSONResponse(
            status_code=200,
            content={
                "message": f"Processed {processed_count} files from {folder_path}",
                "total_files": 1,
                "processed": processed_count,
                "errors": errors
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.get("/get-systems")
async def get_systems(db: Session = Depends(get_db)):
    systems = db.query(filepathEntry).all()
    return [
        {
            "id": system.id,
            "sap_system_id": system.sap_system_id,
            "app_server_instance": system.app_server_instance,
            "file_path": system.file_path
        }
        for system in systems
    ]


@router.get("/get-last-processed-files")
async def get_last_processed_files(db: Session = Depends(get_db)):
    last_processed_files = db.query(lastfileEntry).all()
    return [
        {
            "sap_system_id" : last_processed_file.sap_system_id,
            "app_server_instance" : last_processed_file.app_server_instance,
            "file_name" : last_processed_file.file_name,
            "file_path": last_processed_file.file_path,
            "date_processed" : last_processed_file.date_processed

        }
        for last_processed_file in last_processed_files
    ]

@router.get("/job_history/", response_model=list[FileCheckResponse])
async def get_files(
    date: date = Query(None),
    sap_system_id: str = Query(None),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(FilecheckerEntry)

        if date:
            query = query.filter(func.date(FilecheckerEntry.date) == date)
        if sap_system_id:
            query = query.filter(FilecheckerEntry.sap_system_id == sap_system_id)

        entries = query.all()

        results = []
        for entry in entries:
            results.append({
                "file_id": entry.file_id,
                "last_file_processed": entry.last_file_processed,
                "date": entry.date.date(),
                "sap_system_id": entry.sap_system_id,
                "file_path": entry.file_path
            })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))












@router.get("/logs/params/", response_model=LogEntryResponse)
async def filter_logs_by_every_params(
        start_date: date = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: date = Query(None, description="End date (YYYY-MM-DD)"),
        t_code =Query(None),
        program=Query(None),
        criticality=Query(None),
        user=Query(None),
        sap_system_id=Query(None),
        db: Session = Depends(get_db)
):
    try:
        start_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_str = end_date.strftime("%Y-%m-%d") if end_date else None
        query = db.query(LogEntry)

        if start_str and end_str:
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="Start date must be before end date")
            query = query.filter(LogEntry.date >= start_str, LogEntry.date <= end_str)
        elif start_str:
            query = query.filter(LogEntry.date >= start_str)
        elif end_str:
            query = query.filter(LogEntry.date <= end_str)
        if t_code is not None:
            query = query.filter(LogEntry.transaction_code == t_code)
        if program is not None:
            query = query.filter(LogEntry.program == program)
        if criticality is not None:
            query = query.filter(LogEntry.criticality == criticality)
        if user is not None:
            query = query.filter(LogEntry.user == user)
        if sap_system_id is not None:
            query= query.filter(LogEntry.sap_system_id ==sap_system_id)
        total_logs = query.count()  # Get the total count
        logs = query.order_by(LogEntry.date.desc(), LogEntry.time.desc()).all()

        return {
            "total_logs": total_logs,
            "logs": logs
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")






@router.get("/logs/download/")
async def download_logs_as_csv(
        start_date: date = Query(None),
        end_date: date = Query(None),
        t_code: str = Query(None),
        program: str = Query(None),
        criticality: str = Query(None),
        user: str = Query(None),
        sap_system_id: str = Query(None),
        db: Session = Depends(get_db)
):
    try:
        start_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_str = end_date.strftime("%Y-%m-%d") if end_date else None
        query = db.query(LogEntry)

        if start_str and end_str:
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="Start date must be before end date")
            query = query.filter(LogEntry.date >= start_str, LogEntry.date <= end_str)
        elif start_str:
            query = query.filter(LogEntry.date >= start_str)
        elif end_str:
            query = query.filter(LogEntry.date <= end_str)
        if t_code is not None:
            query = query.filter(LogEntry.transaction_code == t_code)
        if program is not None:
            query = query.filter(LogEntry.program == program)
        if criticality is not None:
            query = query.filter(LogEntry.criticality == criticality)
        if user is not None:
            query = query.filter(LogEntry.user == user)
        if sap_system_id is not None:
            query = query.filter(LogEntry.sap_system_id == sap_system_id)

        logs = query.order_by(LogEntry.date.desc(), LogEntry.time.desc()).all()
        if not logs:
            return Response(content="No logs found for the given filters.", status_code=404)
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "SAP_SYSTEM_ID", "APP_SERVER_INSTANCE", "MESSAGE_IDENTIFIER","MESSAGE_GROUP","SUB_CLASS","DATE","TIME","OS_NUMBER","WORK_PROCESS_NUMBER",
            "SAP_PROCESS","CLIENT","FILE_NUMBER","SHORT_TERMINAL_NAME" ,"USER", "TRANSACTION_CODE",
                         "PROGRAM", "LONG_TERMINAL_NAME", "LAST_ADDRESS_ROUTED","FIRST_VARIABLE","SECOND_VARIABLE","THIRD_VARIABLE",
            "AUDIT_LOG_MSG","AUDIT_CLASS","MSG_SEVERITY","CRITICALITY","OTHER_VARIABLES"])

        for log in logs:

            writer.writerow([
                log.sap_system_id or "",
                log.app_server_instance or "",
                log.message_identifier or "",
                log.syslog_msg_group or "",
                log.sub_name or "",
                log.date or "",
                log.time or "",
                log.operating_system_number or "",
                log.work_process_number or "",
                log.sap_process or "",
                log.client or "",
                log.file_number or "",
                log.short_terminal_name or "",
                log.user or "",
                log.transaction_code or "",
                log.program or "",
                log.long_terminal_name or "",
                log.last_address_routed_no_of_variables or "",
                log.first_variable_value or "",
                log.second_variable_value or "",
                log.third_variable_value or "",
                log.audit_log_msg_text or "",
                log.audit_class or "",
                log.message_severity or "",
                log.criticality or "",
                log.other_variable_values or ""

            ])

        output.seek(0)

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="logs.csv"'}
        )

    except Exception as e:
        return Response(content=f"Server error: {str(e)}", status_code=500)
