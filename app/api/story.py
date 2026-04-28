import json

from app.core.agent import client, writer_agent
from app.core.config import settings


def start_written_story(
    character_name: str,
    character_personality: str,
    drawing_description: str,
    situation_description: str = "",
) -> str:
    scene = situation_description.strip()
    if not scene:
        scene = "un entorno generico, luminoso y amigable"

    prompt = (
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

    response = client.responses.create(
        model=writer_agent.model,
        instructions=writer_agent.role,
        input=prompt,
        temperature=settings.openai_temperature,
        max_output_tokens=settings.openai_max_tokens,
    )

    return response.output_text.strip()


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
    ending_instruction = (
        "- Cierra la aventura con un final satisfactorio y tierno.\n"
        "- No dejes una nueva situacion abierta.\n"
    )
    continuation_instruction = (
        "- Termina con una nueva situacion abierta para que el usuario pueda elegir otra vez.\n"
        "- No incluyas opciones numeradas.\n"
    )

    prompt = (
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

    response = client.responses.create(
        model=writer_agent.model,
        instructions=writer_agent.role,
        input=prompt,
        temperature=settings.openai_temperature,
        max_output_tokens=settings.openai_max_tokens,
    )

    return response.output_text.strip()
