import json
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def make_png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color=(255, 255, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_healthcheck_returns_status_and_version() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "version" in response.json()


def test_describe_character_requires_image_upload() -> None:
    response = client.post(
        "/api/characters/describe",
        files={"image": ("note.txt", b"hola", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Solo se permiten archivos de imagen."


def test_describe_character_rejects_unsupported_image_format() -> None:
    response = client.post(
        "/api/characters/describe",
        files={"image": ("drawing.heic", b"fake-heic", "image/heic")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Formato no compatible. Usa PNG, JPEG, GIF o WEBP."


def test_describe_character_rejects_invalid_image_bytes() -> None:
    response = client.post(
        "/api/characters/describe",
        files={"image": ("drawing.png", b"not-a-real-image", "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "La imagen no es valida o esta dañada. Sube un PNG, JPEG, GIF o WEBP."
    )


def test_describe_character_returns_drawing_description(monkeypatch) -> None:
    def fake_extract_drawing_description(**kwargs) -> str:
        assert kwargs["content_type"] == "image/png"
        assert kwargs["character_name"] == "Luna"
        return "Una nina con capa roja."

    monkeypatch.setattr("app.routes.character.extract_drawing_description", fake_extract_drawing_description)

    response = client.post(
        "/api/characters/describe",
        data={
            "character_name": "Luna",
            "character_personality": "curiosa",
        },
        files={"image": ("drawing.png", make_png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == {"drawing_description": "Una nina con capa roja."}


def test_story_start_streams_text_and_returns_state(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routes.story.stream_start_written_story",
        lambda **kwargs: iter(["Habia ", "una vez"]),
    )

    response = client.post(
        "/api/stories/start",
        json={
            "character_name": "Luna",
            "character_personality": "curiosa",
            "drawing_description": "Una nina con capa roja",
            "situation_description": "un bosque brillante",
        },
    )

    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.strip().splitlines()]
    assert events[0] == {"type": "delta", "text": "Habia "}
    assert events[1] == {"type": "delta", "text": "una vez"}
    assert events[2]["type"] == "done"
    assert events[2]["story_text"] == "Habia una vez"
    assert events[2]["story_state"]["phase"] == "choice_1"
    assert events[2]["can_generate_image"] is True


def test_story_choices_returns_generated_options(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routes.story.generate_story_choices",
        lambda **kwargs: ["Explorar el lugar misterioso", "Pedir ayuda a un nuevo amigo"],
    )

    response = client.post(
        "/api/stories/choices",
        json={
            "story_text": "Habia una vez",
            "character_name": "Luna",
            "character_personality": "curiosa",
        },
    )

    assert response.status_code == 200
    assert response.json()["choices"] == [
        "Explorar el lugar misterioso",
        "Pedir ayuda a un nuevo amigo",
    ]


def test_story_continue_streams_updated_scene(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routes.story.stream_continue_written_story",
        lambda **kwargs: iter(["La puerta ", "se abrio."]),
    )

    response = client.post(
        "/api/stories/continue",
        json={
            "story_text": "Luna encontro una puerta.",
            "selected_choice": "Abrir la puerta",
            "character_name": "Luna",
            "character_personality": "curiosa",
            "story_state": {
                "phase": "choice_1",
                "choices": [],
                "image_count": 1,
                "max_images": 3,
            },
        },
    )

    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.strip().splitlines()]
    assert events[-1]["type"] == "done"
    assert events[-1]["current_scene_text"] == "La puerta se abrio."
    assert events[-1]["story_text"] == "Luna encontro una puerta.\n\nLa puerta se abrio."
    assert events[-1]["story_state"]["phase"] == "choice_2"
    assert events[-1]["can_generate_image"] is True


def test_generate_image_returns_base64_payload(monkeypatch) -> None:
    monkeypatch.setattr("app.routes.images.generate_character_image", lambda **kwargs: b"image-bytes")

    response = client.post(
        "/api/images/generate",
        json={
            "character_name": "Luna",
            "character_personality": "curiosa",
            "drawing_description": "Una nina con capa roja",
            "situation_description": "un bosque brillante",
            "story_context": "Habia una vez",
            "chosen_action": "Abrir la puerta",
            "story_state": {
                "phase": "choice_1",
                "choices": [],
                "image_count": 1,
                "max_images": 3,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["media_type"] == "image/png"
    assert response.json()["image_base64"] == "aW1hZ2UtYnl0ZXM="
    assert response.json()["story_state"]["image_count"] == 2


def test_generate_image_rejects_requests_after_reaching_limit(monkeypatch) -> None:
    monkeypatch.setattr("app.routes.images.generate_character_image", lambda **kwargs: b"image-bytes")

    response = client.post(
        "/api/images/generate",
        json={
            "character_name": "Luna",
            "character_personality": "curiosa",
            "drawing_description": "Una nina con capa roja",
            "situation_description": "un bosque brillante",
            "story_context": "Habia una vez",
            "chosen_action": "Abrir la puerta",
            "story_state": {
                "phase": "choice_1",
                "choices": [],
                "image_count": 3,
                "max_images": 3,
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "La historia ya ha alcanzado el maximo de ilustraciones permitidas."
    )
