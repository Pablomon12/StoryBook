from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.character import extract_drawing_description
from app.schemas import CharacterDescriptionResponse

router = APIRouter(prefix="/characters", tags=["characters"])


@router.post("/describe", response_model=CharacterDescriptionResponse)
async def describe_character(
    image: UploadFile = File(...),
    character_name: str = Form(default=""),
    character_personality: str = Form(default=""),
) -> CharacterDescriptionResponse:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")

    drawing_description = extract_drawing_description(
        uploaded_image=image_bytes,
        content_type=image.content_type,
        character_name=character_name,
        character_personality=character_personality,
    )
    return CharacterDescriptionResponse(drawing_description=drawing_description)
