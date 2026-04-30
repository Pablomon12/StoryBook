import base64
import logging

from fastapi import APIRouter, HTTPException
from openai import OpenAIError

from app.api.character import generate_character_image
from app.schemas import ImageGenerateRequest, ImageGenerateResponse

router = APIRouter(prefix="/images", tags=["images"])
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=ImageGenerateResponse)
def generate_image(payload: ImageGenerateRequest) -> ImageGenerateResponse:
    try:
        image_bytes = generate_character_image(
            character_name=payload.character_name,
            character_personality=payload.character_personality,
            drawing_description=payload.drawing_description,
            situation_description=payload.situation_description,
            story_context=payload.story_context,
            chosen_action=payload.chosen_action,
        )
    except OpenAIError as exc:
        logger.exception("OpenAI image generation failed")
        raise HTTPException(status_code=502, detail=f"OpenAI no pudo generar la ilustracion: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected image generation failure")
        raise HTTPException(status_code=500, detail="Error interno al generar la ilustracion.") from exc

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    return ImageGenerateResponse(image_base64=image_base64)
