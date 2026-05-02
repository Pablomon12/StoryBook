from io import BytesIO

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from openai import BadRequestError
from PIL import Image, UnidentifiedImageError

from app.api.character import extract_drawing_description
from app.schemas import CharacterDescriptionResponse

router = APIRouter(prefix="/characters", tags=["characters"])
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


@router.post("/describe", response_model=CharacterDescriptionResponse)
async def describe_character(
    image: UploadFile = File(...),
    character_name: str = Form(default=""),
    character_personality: str = Form(default=""),
) -> CharacterDescriptionResponse:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported.")
    if image.content_type not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Formato no compatible. Usa PNG, JPEG, GIF o WEBP.",
        )

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")

    try:
        with Image.open(BytesIO(image_bytes)) as uploaded:
            uploaded.verify()
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise HTTPException(
            status_code=400,
            detail="La imagen no es valida o esta dañada. Sube un PNG, JPEG, GIF o WEBP.",
        ) from None

    try:
        drawing_description = extract_drawing_description(
            uploaded_image=image_bytes,
            content_type=image.content_type,
            character_name=character_name,
            character_personality=character_personality,
        )
    except BadRequestError as exc:
        raise HTTPException(
            status_code=400,
            detail="No se pudo analizar la imagen. Prueba con un PNG, JPEG, GIF o WEBP valido.",
        ) from exc

    return CharacterDescriptionResponse(drawing_description=drawing_description)
