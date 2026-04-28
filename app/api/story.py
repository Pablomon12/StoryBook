import json
from collections.abc import Iterator

from app.core.agent import client, writer_agent
from app.core.config import settings


def build_start_story_prompt(
    character_name: str,
    character_personality: str,
    drawing_description: str,
    situation_description: str = "",
) -> str:
    scene = situation_description.strip()
    if not scene:
        scene = "un entorno generico, luminoso y amigable"

    return (
        "Crea el inicio de una historia infantil en espanol usando estos datos.\n\n"
        f"Nombre del personaje: {character_name or 'Personaje sin nombre'}.\n"
        f"Personalidad del personaje: {character_personality or 'curioso y amable'}.\n"
        f"Descripcion visual del personaje: {drawing_description}.\n"
        f"Situacion inicial: {scene}.\n\n"
        "Requisitos:\n"
        "- Escribe entre 2 y 4 parrafos breves.\n"
        "- Usa un tono imaginativo, claro y apropiado para ninos.\n"
        "- Presenta al personaje y el lugar donde empieza la aventura.\n"
        "- Termina con una pequena situacion abierta para continuar la historia.\n"
        "- No incluyas opciones numeradas todavia."
    )


def build_continue_story_prompt(
    story_text: str,
    selected_choice: str,
    character_name: str,
    character_personality: str,
    is_ending: bool = False,
) -> str:
    ending_instruction = (
        "- Cierra la aventura con un final satisfactorio y tierno.\n"
        "- No dejes una nueva situacion abierta.\n"
    )
    continuation_instruction = (
        "- Termina con una nueva situacion abierta para que el usuario pueda elegir otra vez.\n"
        "- No incluyas opciones numeradas.\n"
    )

    return (
        "Continua esta historia infantil en espanol respetando la opcion elegida por el usuario.\n\n"
        f"Nombre del personaje: {character_name or 'Personaje sin nombre'}.\n"
        f"Personalidad del personaje: {character_personality or 'curioso y amable'}.\n"
        f"Historia hasta ahora:\n{story_text}\n\n"
        f"Opcion elegida: {selected_choice}.\n\n"
        "Requisitos:\n"
        "- Escribe entre 2 y 4 parrafos breves.\n"
        "- Haz que la opcion elegida tenga consecuencias claras en la escena.\n"
        "- Manten un tono imaginativo, claro y apropiado para ninos.\n"
        f"{ending_instruction if is_ending else continuation_instruction}"
    )


def stream_story_text(prompt: str) -> Iterator[str]:
    with client.responses.stream(
        model=writer_agent.model,
        instructions=writer_agent.role,
        input=prompt,
        temperature=settings.openai_temperature,
        max_output_tokens=settings.openai_max_tokens,
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta


def stream_start_written_story(
    character_name: str,
    character_personality: str,
    drawing_description: str,
    situation_description: str = "",
) -> Iterator[str]:
    prompt = build_start_story_prompt(
        character_name=character_name,
        character_personality=character_personality,
        drawing_description=drawing_description,
        situation_description=situation_description,
    )
    yield from stream_story_text(prompt)


def start_written_story(
    character_name: str,
    character_personality: str,
    drawing_description: str,
    situation_description: str = "",
) -> str:
    chunks = stream_start_written_story(
        character_name=character_name,
        character_personality=character_personality,
        drawing_description=drawing_description,
        situation_description=situation_description,
    )

    return "".join(chunks).strip()


def generate_story_choices(
    story_text: str,
    character_name: str,
    character_personality: str,
) -> list[str]:
    prompt = (
        "Genera exactamente dos opciones breves para continuar esta historia infantil.\n\n"
        f"Nombre del personaje: {character_name or 'Personaje sin nombre'}.\n"
        f"Personalidad del personaje: {character_personality or 'curioso y amable'}.\n"
        f"Historia actual:\n{story_text}\n\n"
        "Responde solo con JSON valido, sin markdown, con esta forma exacta:\n"
        '{"choices": ["opcion 1", "opcion 2"]}\n'
        "Cada opcion debe tener menos de 90 caracteres y empezar con un verbo de accion."
    )

    response = client.responses.create(
        model=writer_agent.model,
        instructions=writer_agent.role,
        input=prompt,
        temperature=settings.openai_temperature,
        max_output_tokens=300,
    )

    try:
        data = json.loads(response.output_text)
        choices = data.get("choices", [])
    except json.JSONDecodeError:
        choices = []

    clean_choices = [choice.strip() for choice in choices if isinstance(choice, str) and choice.strip()]
    if len(clean_choices) >= 2:
        return clean_choices[:2]

    return [
        "Explorar el lugar misterioso",
        "Pedir ayuda a un nuevo amigo",
    ]


def continue_written_story(
    story_text: str,
    selected_choice: str,
    character_name: str,
    character_personality: str,
    is_ending: bool = False,
) -> str:
    chunks = stream_continue_written_story(
        story_text=story_text,
        selected_choice=selected_choice,
        character_name=character_name,
        character_personality=character_personality,
        is_ending=is_ending,
    )

    return "".join(chunks).strip()


def stream_continue_written_story(
    story_text: str,
    selected_choice: str,
    character_name: str,
    character_personality: str,
    is_ending: bool = False,
) -> Iterator[str]:
    prompt = build_continue_story_prompt(
        story_text=story_text,
        selected_choice=selected_choice,
        character_name=character_name,
        character_personality=character_personality,
        is_ending=is_ending,
    )
    yield from stream_story_text(prompt)
