from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes import character, health, images, story

app = FastAPI(title="Story Creator API", version=settings.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(character.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(story.router, prefix="/api")
