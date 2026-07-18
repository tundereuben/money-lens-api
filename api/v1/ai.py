import shutil
from fastapi import APIRouter, Depends, File, UploadFile
from modules.ai import google_ai_service as ai_service
import tempfile
import os
from models.user import User
from shared.dependencies import get_current_user

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/voice", summary="Generate expense payload using AI")
async def upload_voice(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):

    # Enforce authentication before processing uploaded audio.
    _ = current_user

    suffix = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_file_path = temp_file.name

    try:
        result = ai_service.extract_transaction(temp_file_path)
        return result
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)