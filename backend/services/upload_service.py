import os
from fastapi import UploadFile

# Upload folder path
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")

# Ensure the folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_upload(user_id: str, file: UploadFile) -> str:
    """
    Save uploaded file to the uploads folder with a user_id prefix.
    """
    filename = f"{user_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Save the file
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Return relative path
    return f"uploads/{filename}"
