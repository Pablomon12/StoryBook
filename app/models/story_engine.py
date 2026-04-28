from app.story import CharacterProfile, StoryPhase, StoryState, StoryTurn


def create_initial_state() -> StoryState:
    return StoryState()


def set_character(state: StoryState, character: CharacterProfile) -> StoryState:
    state.character = character
    state.phase = StoryPhase.OPENING
    return state


def add_story_text(state: StoryState, text: str) -> StoryState:
    state.turns.append(
        StoryTurn(
            phase=state.phase,
            text=text,
        )
    )
    return state


def register_choice(state: StoryState, choice: str) -> StoryState:
    state.choices.append(choice)

    if state.phase == StoryPhase.CHOICE_1:
        state.phase = StoryPhase.CONTINUATION
    elif state.phase == StoryPhase.CHOICE_2:
        state.phase = StoryPhase.ENDING

    return state


def move_to_next_checkpoint(state: StoryState) -> StoryState:
    if state.phase == StoryPhase.OPENING:
        state.phase = StoryPhase.CHOICE_1
    elif state.phase == StoryPhase.CONTINUATION:
        state.phase = StoryPhase.CHOICE_2
    elif state.phase == StoryPhase.ENDING:
        state.phase = StoryPhase.FINISHED

    return state


def can_generate_image(state: StoryState) -> bool:
    return state.image_count < state.max_images


def register_generated_image(state: StoryState) -> StoryState:
    if can_generate_image(state):
        state.image_count += 1
    return state


def is_finished(state: StoryState) -> bool:
    return state.phase == StoryPhase.FINISHED
