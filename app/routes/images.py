import base64
import logging

from fastapi import APIRouter, HTTPException
from openai import OpenAIError

from app.api.character import generate_character_image
from app.models.story_engine import can_generate_image, register_generated_image
from app.schemas import (
    ImageGenerateRequest,
    ImageGenerateResponse,
    story_state_from_payload,
    story_state_to_payload,
)

router = APIRouter(prefix="/images", tags=["images"])
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=ImageGenerateResponse)
def generate_image(payload: ImageGenerateRequest) -> ImageGenerateResponse:
    state = story_state_from_payload(payload.story_state)
    if not can_generate_image(state):
        raise HTTPException(
            status_code=400,
            detail="La historia ya ha alcanzado el maximo de ilustraciones permitidas.",
        )

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
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI no pudo generar la ilustracion: {exc}",
        ) from exc

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    updated_state = register_generated_image(state)
    return ImageGenerateResponse(
        image_base64=image_base64,
        story_state=story_state_to_payload(updated_state),
    )
