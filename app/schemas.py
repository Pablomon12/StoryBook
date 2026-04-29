from pydantic import BaseModel, Field

from app.story import StoryPhase, StoryState


class StoryStatePayload(BaseModel):
    phase: StoryPhase = StoryPhase.START
    choices: list[str] = Field(default_factory=list)
    image_count: int = 0
    max_images: int = 3


class CharacterDescriptionResponse(BaseModel):
    drawing_description: str


class StoryStartRequest(BaseModel):
    character_name: str = Field(default="", max_length=30)
    character_personality: str = Field(default="", max_length=80)
    drawing_description: str = Field(min_length=1)
    situation_description: str = Field(default="", max_length=300)


class StoryChoicesRequest(BaseModel):
    story_text: str = Field(min_length=1)
    character_name: str = Field(default="", max_length=30)
    character_personality: str = Field(default="", max_length=80)


class StoryChoicesResponse(BaseModel):
    choices: list[str]


class StoryContinueRequest(BaseModel):
    story_text: str = Field(min_length=1)
    selected_choice: str = Field(min_length=1, max_length=120)
    character_name: str = Field(default="", max_length=30)
    character_personality: str = Field(default="", max_length=80)
    story_state: StoryStatePayload


class ImageGenerateRequest(BaseModel):
    character_name: str = Field(default="", max_length=30)
    character_personality: str = Field(default="", max_length=80)
    drawing_description: str = Field(min_length=1)
    situation_description: str = Field(default="", max_length=300)
    story_context: str = Field(default="", max_length=5000)
    chosen_action: str = Field(default="", max_length=120)


class ImageGenerateResponse(BaseModel):
    image_base64: str
    media_type: str = "image/png"


class HealthResponse(BaseModel):
    status: str
    version: str


def story_state_from_payload(payload: StoryStatePayload) -> StoryState:
    return StoryState(
        phase=payload.phase,
        choices=list(payload.choices),
        image_count=payload.image_count,
        max_images=payload.max_images,
    )


def story_state_to_payload(state: StoryState) -> StoryStatePayload:
    return StoryStatePayload(
        phase=state.phase,
        choices=list(state.choices),
        image_count=state.image_count,
        max_images=state.max_images,
    )
