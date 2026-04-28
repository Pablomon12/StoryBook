from dataclasses import dataclass, field
from enum import Enum


class StoryPhase(str, Enum):
    START = "start"
    OPENING = "opening"
    CHOICE_1 = "choice_1"
    CONTINUATION = "continuation"
    CHOICE_2 = "choice_2"
    ENDING = "ending"
    FINISHED = "finished"


@dataclass
class CharacterProfile:
    name: str
    description: str
    personality: str = ""


@dataclass
class StoryTurn:
    phase: StoryPhase
    text: str = ""
    user_choice: str | None = None


@dataclass
class StoryState:
    phase: StoryPhase = StoryPhase.START
    character: CharacterProfile | None = None
    turns: list[StoryTurn] = field(default_factory=list)
    choices: list[str] = field(default_factory=list)
    image_count: int = 0
    max_images: int = 3
