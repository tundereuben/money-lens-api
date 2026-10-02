import shutil
import asyncio
from fastapi import APIRouter, Depends, File, UploadFile
from modules.ai import google_ai_service as ai_service
import tempfile
import os
from sqlalchemy.orm import Session, joinedload
from models.category import UserCategory
from models.user import User
from schemas.category import CategoryType
from shared.dependencies import get_current_user, get_db

router = APIRouter(prefix="/ai", tags=["AI"])


def save_upload_to_temporary_file(upload: UploadFile, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        shutil.copyfileobj(upload.file, temp_file)
        return temp_file.name


@router.post("/voice", summary="Generate expense payload using AI")
async def upload_voice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_categories = (
        db.query(UserCategory)
        .options(joinedload(UserCategory.system_category))
        .filter(UserCategory.user_id == current_user.id, UserCategory.is_active.is_(True))
        .all()
    )
    categories = [
        {
            "id": category.id,
            "name": category.system_category.name,
        }
        for category in user_categories
        if category.system_category.category_type == CategoryType.EXPENSE.value
    ]

    suffix = os.path.splitext(file.filename)[1]

    temp_file_path = await asyncio.to_thread(save_upload_to_temporary_file, file, suffix)

    try:
        result = ai_service.extract_transaction(temp_file_path, categories)
        return result
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)