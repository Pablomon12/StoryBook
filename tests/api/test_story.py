from types import SimpleNamespace

from app.api import story


class FakeStream:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        return iter(self.events)

    def __exit__(self, exc_type, exc, exc_tb):
        return None


def test_stream_story_text_yields_only_text_deltas(monkeypatch) -> None:
    events = [
        SimpleNamespace(type="response.created", delta="ignored"),
        SimpleNamespace(type="response.output_text.delta", delta="Habia "),
        SimpleNamespace(type="response.output_text.delta", delta="una vez"),
        SimpleNamespace(type="response.completed", delta="ignored"),
    ]

    def fake_stream(**kwargs):
        return FakeStream(events)

    monkeypatch.setattr(story.client.responses, "stream", fake_stream)

    assert list(story.stream_story_text("prompt")) == ["Habia ", "una vez"]


def test_start_written_story_joins_streamed_chunks(monkeypatch) -> None:
    monkeypatch.setattr(
        story,
        "stream_start_written_story",
        lambda **kwargs: iter(["  Luna ", "salio a explorar.  "]),
    )

    result = story.start_written_story(
        character_name="Luna",
        character_personality="curiosa",
        drawing_description="Una nina con botas azules",
    )

    assert result == "Luna salio a explorar."


def test_continue_written_story_joins_streamed_chunks(monkeypatch) -> None:
    monkeypatch.setattr(
        story,
        "stream_continue_written_story",
        lambda **kwargs: iter(["  La puerta ", "se abrio.  "]),
    )

    result = story.continue_written_story(
        story_text="Luna encontro una puerta.",
        selected_choice="Abrir la puerta",
        character_name="Luna",
        character_personality="curiosa",
    )

    assert result == "La puerta se abrio."
