import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from datetime import datetime

from app.models.last_file_processed import lastfileEntry
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

@router.get("/logs/", response_model=List[LogEntryResponse])
async def get_logs(db: Session = Depends(get_db)):
    try:
        return db.query(LogEntry).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")