# backend/services/upload_service.py
import os
from fastapi import UploadFile
from pathlib import Path

UPLOAD_DIR = Path("backend/uploads")

def save_upload(user_id: str, file: UploadFile) -> str:
    """
    Save the uploaded file in the uploads/ directory under the user's folder.
    """
    user_folder = UPLOAD_DIR / user_id
    user_folder.mkdir(parents=True, exist_ok=True)

    file_path = user_folder / file.filename

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return str(file_path)
