import base64

from fastapi import APIRouter

from app.api.character import generate_character_image
from app.schemas import ImageGenerateRequest, ImageGenerateResponse

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/generate", response_model=ImageGenerateResponse)
def generate_image(payload: ImageGenerateRequest) -> ImageGenerateResponse:
    image_bytes = generate_character_image(
        character_name=payload.character_name,
        character_personality=payload.character_personality,
        drawing_description=payload.drawing_description,
        situation_description=payload.situation_description,
        story_context=payload.story_context,
        chosen_action=payload.chosen_action,
    )
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    return ImageGenerateResponse(image_base64=image_base64)
