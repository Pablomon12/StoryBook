import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.story import (
    append_story_text,
    generate_story_choices,
    stream_continue_written_story,
    stream_start_written_story,
)
from app.models.story_engine import (
    add_story_text,
    can_generate_image,
    create_initial_state,
    is_finished,
    move_to_next_checkpoint,
    register_choice,
    set_character,
)
from app.schemas import (
    StoryChoicesRequest,
    StoryChoicesResponse,
    StoryContinueRequest,
    StoryStartRequest,
    story_state_from_payload,
    story_state_to_payload,
)
from app.story import CharacterProfile, StoryPhase

router = APIRouter(prefix="/stories", tags=["stories"])


def _stream_event(payload: dict[str, object]) -> bytes:
    return f"{json.dumps(payload)}\n".encode("utf-8")


def _opening_story_events(payload: StoryStartRequest) -> Iterator[bytes]:
    chunks: list[str] = []
    for chunk in stream_start_written_story(
        character_name=payload.character_name,
        character_personality=payload.character_personality,
        drawing_description=payload.drawing_description,
        situation_description=payload.situation_description,
    ):
        chunks.append(chunk)
        yield _stream_event({"type": "delta", "text": chunk})

    opening_text = "".join(chunks).strip()
    character = CharacterProfile(
        name=payload.character_name,
        description=payload.drawing_description,
        personality=payload.character_personality,
    )
    state = set_character(create_initial_state(), character)
    state = add_story_text(state, opening_text)
    state = move_to_next_checkpoint(state)

    yield _stream_event(
        {
            "type": "done",
            "story_text": opening_text,
            "current_scene_text": opening_text,
            "story_state": story_state_to_payload(state).model_dump(mode="json"),
            "is_finished": is_finished(state),
            "can_generate_image": can_generate_image(state),
        }
    )


def _continuation_story_events(payload: StoryContinueRequest) -> Iterator[bytes]:
    state = story_state_from_payload(payload.story_state)
    if state.phase == StoryPhase.FINISHED:
        raise HTTPException(status_code=400, detail="The story is already finished.")

    state = register_choice(state, payload.selected_choice)
    ending_turn = state.phase == StoryPhase.ENDING

    chunks: list[str] = []
    for chunk in stream_continue_written_story(
        story_text=payload.story_text,
        selected_choice=payload.selected_choice,
        character_name=payload.character_name,
        character_personality=payload.character_personality,
        is_ending=ending_turn,
    ):
        chunks.append(chunk)
        yield _stream_event({"type": "delta", "text": chunk})

    current_scene_text = "".join(chunks).strip()
    updated_story_text = append_story_text(payload.story_text, current_scene_text)
    state = add_story_text(state, current_scene_text)
    state = move_to_next_checkpoint(state)

    yield _stream_event(
        {
            "type": "done",
            "story_text": updated_story_text,
            "current_scene_text": current_scene_text,
            "story_state": story_state_to_payload(state).model_dump(mode="json"),
            "is_finished": is_finished(state),
            "can_generate_image": can_generate_image(state),
        }
    )


@router.post("/start")
def start_story(payload: StoryStartRequest) -> StreamingResponse:
    return StreamingResponse(_opening_story_events(payload), media_type="application/x-ndjson")


@router.post("/choices", response_model=StoryChoicesResponse)
def story_choices(payload: StoryChoicesRequest) -> StoryChoicesResponse:
    choices = generate_story_choices(
        story_text=payload.story_text,
        character_name=payload.character_name,
        character_personality=payload.character_personality,
    )
    return StoryChoicesResponse(choices=choices)


@router.post("/continue")
def continue_story(payload: StoryContinueRequest) -> StreamingResponse:
    return StreamingResponse(_continuation_story_events(payload), media_type="application/x-ndjson")
