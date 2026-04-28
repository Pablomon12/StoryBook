from dataclasses import dataclass

from openai import OpenAI

from app.core.config import settings


client = OpenAI(api_key=settings.openai_api_key)


@dataclass(frozen=True)
class Agent:
    name: str
    model: str
    role: str


writer_agent = Agent(
    name="writer",
    model=settings.openai_model_write,
    role="Escribe historias infantiles a partir de la descripción de un personaje y la fase de la historia en la que se encuentra.",
)

vision_agent = Agent(
    name="vision",
    model=settings.openai_model_vision,
    role="Analiza dibujos e identifica personaje, objetos, colores y estilo.",
)

image_agent = Agent(
    name="image",
    model=settings.openai_model_image,
    role="Genera imagenes para acompanar la historia.",
)
