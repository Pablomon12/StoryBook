from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


APP_MODULE_PATH = Path(__file__).resolve().parents[1] / "app.py"
APP_SPEC = spec_from_file_location("streamlit_app_module", APP_MODULE_PATH)
assert APP_SPEC is not None
assert APP_SPEC.loader is not None
APP_MODULE = module_from_spec(APP_SPEC)
APP_SPEC.loader.exec_module(APP_MODULE)

append_story_text = APP_MODULE.append_story_text
collect_streamed_text = APP_MODULE.collect_streamed_text
split_story_text = APP_MODULE.split_story_text
stream_text_into_placeholder = APP_MODULE.stream_text_into_placeholder


class FakePlaceholder:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def markdown(self, message: str) -> None:
        self.messages.append(message)


def test_append_story_text_keeps_existing_paragraphs() -> None:
    result = append_story_text("Luna encontro un mapa.", "Decidio seguir el camino dorado.")

    assert result == "Luna encontro un mapa.\n\nDecidio seguir el camino dorado."


def test_split_story_text_separates_latest_scene_from_history() -> None:
    history, current = split_story_text(
        "Luna encontro un mapa.\n\nDecidio seguir el camino dorado.",
        "Decidio seguir el camino dorado.",
    )

    assert history == "Luna encontro un mapa."
    assert current == "Decidio seguir el camino dorado."


def test_collect_streamed_text_reports_progress_and_final_text() -> None:
    updates: list[tuple[str, bool]] = []

    result = collect_streamed_text(
        ["Habia ", "una vez"],
        on_update=lambda text, is_streaming: updates.append((text, is_streaming)),
    )

    assert result == "Habia una vez"
    assert updates == [
        ("Habia ", True),
        ("Habia una vez", True),
        ("Habia una vez", False),
    ]


def test_stream_text_into_placeholder_writes_cursor_while_streaming() -> None:
    placeholder = FakePlaceholder()

    result = stream_text_into_placeholder(["Luna ", "corrio."], placeholder)

    assert result == "Luna corrio."
    assert placeholder.messages == [
        "Luna ▌",
        "Luna corrio.▌",
        "Luna corrio.",
    ]
