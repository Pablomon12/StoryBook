import base64
from typing import BinaryIO

from app.core.agent import client, image_agent, vision_agent
from app.core.config import settings


def extract_drawing_description(
    uploaded_image: BinaryIO,
    character_name: str = "",
    character_personality: str = "",
) -> str:
    image_bytes = uploaded_image.getvalue()
    content_type = getattr(uploaded_image, "type", None) or "image/png"
    image_data = base64.b64encode(image_bytes).decode("utf-8")
    image_url = f"data:{content_type};base64,{image_data}"

    prompt = (
        "Analiza el dibujo subido por el usuario y extrae una descripcion breve "
        "del personaje. Incluye apariencia, colores principales, objetos visibles "
        "y estilo del dibujo. Responde en espanol en 3 o 4 frases."
    )

    if character_name:
        prompt += f"\nNombre del personaje: {character_name}."
    if character_personality:
        prompt += f"\nPersonalidad indicada por el usuario: {character_personality}."

    response = client.responses.create(
        model=vision_agent.model,
        instructions=vision_agent.role,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image_url},
                ],
            }
        ],
        temperature=settings.openai_temperature,
        max_output_tokens=settings.openai_max_tokens,
    )
    return response.output_text.strip()


def build_character_image_prompt(
    character_name: str,
    character_personality: str,
    drawing_description: str,
    situation_description: str = "",
    story_context: str = "",
    chosen_action: str = "",
) -> str:
    scene = situation_description.strip()
    if not scene:
        scene = "un entorno generico, luminoso y amigable"

    context = story_context.strip()
    action = chosen_action.strip()

    story_details = ""
    if context:
        story_details += f"Contexto de la historia hasta ahora: {context}.\n"
    if action:
        story_details += f"Accion elegida para esta escena: {action}.\n"

    return (
        "Genera una ilustracion infantil basada en el personaje descrito. "
        "Manten coherencia con su apariencia original y evita cambiar sus rasgos principales.\n\n"
        f"Nombre del personaje: {character_name or 'Personaje sin nombre'}.\n"
        f"Personalidad: {character_personality or 'amable y curioso'}.\n"
        f"Descripcion visual del dibujo original: {drawing_description}.\n"
        f"Situacion o entorno: {scene}.\n\n"
        f"{story_details}"
        "Estilo: ilustracion colorida, clara, expresiva y apropiada para un cuento infantil."
    )


def generate_character_image(
    character_name: str,
    character_personality: str,
    drawing_description: str,
    situation_description: str = "",
    story_context: str = "",
    chosen_action: str = "",
    size: str = "1024x1024",
) -> bytes:
    prompt = build_character_image_prompt(
        character_name=character_name,
        character_personality=character_personality,
        drawing_description=drawing_description,
        situation_description=situation_description,
        story_context=story_context,
        chosen_action=chosen_action,
    )

    response = client.images.generate(
        model=image_agent.model,
        prompt=prompt,
        size=size,
    )

    image_base64 = response.data[0].b64_json
    return base64.b64decode(image_base64)
