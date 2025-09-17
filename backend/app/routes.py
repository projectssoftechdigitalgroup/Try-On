from fastapi import APIRouter, UploadFile, File, Form
from backend.services.upload_service import save_upload  # adjust path if needed


router = APIRouter()

@router.post("/upload/")
async def upload_image(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    saved_path = save_upload(user_id, file)
    return {
        "message": "Image uploaded successfully",
        "path": saved_path
    }
