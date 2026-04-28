from app.api.character import build_character_image_prompt


def test_build_character_image_prompt_includes_story_choice() -> None:
    prompt = build_character_image_prompt(
        character_name="Luna",
        character_personality="valiente",
        drawing_description="Una nina con capa roja y botas azules",
        situation_description="un bosque brillante",
        story_context="Luna encontro una puerta pequena entre los arboles",
        chosen_action="Abrir la puerta misteriosa",
    )

    assert "Luna" in prompt
    assert "Abrir la puerta misteriosa" in prompt
    assert "Luna encontro una puerta pequena entre los arboles" in prompt
