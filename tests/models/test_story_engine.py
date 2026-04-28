from app.models.story_engine import (
    add_story_text,
    create_initial_state,
    is_finished,
    move_to_next_checkpoint,
    register_choice,
    set_character,
)
from app.story import CharacterProfile, StoryPhase


def test_story_phase_transitions_after_two_choices() -> None:
    character = CharacterProfile(name="Luna", description="Capa roja")
    state = set_character(create_initial_state(), character)
    state = add_story_text(state, "Luna empieza la aventura.")
    state = move_to_next_checkpoint(state)

    assert state.phase == StoryPhase.CHOICE_1

    state = register_choice(state, "Explorar el bosque")
    assert state.phase == StoryPhase.CONTINUATION

    state = add_story_text(state, "Luna encuentra una luz.")
    state = move_to_next_checkpoint(state)
    assert state.phase == StoryPhase.CHOICE_2

    state = register_choice(state, "Seguir la luz")
    assert state.phase == StoryPhase.ENDING

    state = add_story_text(state, "Luna vuelve feliz a casa.")
    state = move_to_next_checkpoint(state)

    assert is_finished(state)
    assert state.choices == ["Explorar el bosque", "Seguir la luz"]
