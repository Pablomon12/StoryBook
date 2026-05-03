# Creador de Historias con Dibujos

Aplicación con backend `FastAPI` y frontend `Next.js` que transforma un dibujo subido por el usuario en una historia infantil ilustrada. El modo de despliegue soportado para este proyecto es exclusivamente con `docker compose`.

## Arquitectura

- `app/`: backend FastAPI.
- `app/routes/`: endpoints HTTP.
- `app/api/`: integración con OpenAI para descripción, texto e imagen.
- `app/core/`: configuración y cliente OpenAI.
- `app/models/`: lógica de estado de la historia.
- `app/story.py`: modelos de dominio.
- `frontend/`: interfaz `Next.js` App Router.
- `tests/`: pruebas backend con `pytest`.
- `Dockerfile`: imagen del backend.
- `frontend/Dockerfile`: imagen del frontend.
- `docker-compose.yml`: orquestación completa del stack.

## Requisitos

- Docker Engine
- Docker Compose
- Una `OPENAI_API_KEY` válida

No se documenta ni se soporta despliegue operativo fuera de Docker.

## Configuración

1. Crea el archivo de entorno desde la plantilla:

```bash
cp .env.example .env
```

2. Define al menos la clave de OpenAI y revisa los puertos publicados:

```bash
OPENAI_API_KEY=tu_api_key_de_openai
FRONTEND_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api
INTERNAL_API_BASE_URL=http://api:8000/api
API_HOST_PORT=8001
FRONTEND_HOST_PORT=3000
```

### Variables usadas por `docker compose`

| Variable | Uso |
| --- | --- |
| `OPENAI_API_KEY` | Credencial para descripción del dibujo, generación de texto e imágenes |
| `FRONTEND_ORIGINS` | Orígenes permitidos por CORS en la API, separados por comas |
| `NEXT_PUBLIC_API_BASE_URL` | URL pública de la API consumida por el navegador |
| `INTERNAL_API_BASE_URL` | URL privada entre contenedores para los rewrites del frontend |
| `API_HOST_PORT` | Puerto publicado para la API en la máquina host |
| `FRONTEND_HOST_PORT` | Puerto publicado para el frontend en la máquina host |

Notas:

- `NEXT_PUBLIC_API_BASE_URL` debe apuntar al puerto público real de la API.
- `INTERNAL_API_BASE_URL` debe mantenerse en `http://api:8000/api` salvo que cambie la red interna del stack.
- Si publicas el frontend con otro dominio o puerto, añade ese origen a `FRONTEND_ORIGINS`.

## Despliegue con Docker

1. Construye y arranca los servicios:

```bash
docker compose up --build -d
```

2. Comprueba que ambos contenedores están levantados:

```bash
docker compose ps
```

3. Verifica las URLs principales:

- Frontend: [http://localhost:3000](http://localhost:3000)
- API: [http://localhost:8001](http://localhost:8001)
- Swagger: [http://localhost:8001/docs](http://localhost:8001/docs)
- Healthcheck: [http://localhost:8001/api/health](http://localhost:8001/api/health)

## Funcionamiento de la aplicación

1. El usuario sube un dibujo desde el frontend.
2. `POST /api/characters/describe` analiza la imagen y genera una descripción del personaje.
3. `POST /api/stories/start` inicia la historia en streaming NDJSON.
4. `POST /api/stories/choices` propone dos opciones de continuación.
5. `POST /api/stories/continue` avanza la historia en streaming.
6. `POST /api/images/generate` crea la ilustración de cada escena respetando el límite de imágenes por historia.

Los endpoints de historia `start` y `continue` responden en `application/x-ndjson`. Si se despliega detrás de un proxy, este debe permitir streaming sin buffer.

## Endpoints principales

- `POST /api/characters/describe`
- `POST /api/stories/start`
- `POST /api/stories/choices`
- `POST /api/stories/continue`
- `POST /api/images/generate`
- `GET /api/health`

## Operación

Comandos útiles:

```bash
docker compose logs -f
docker compose logs -f api
docker compose logs -f frontend
docker compose down
```

## Troubleshooting

### Puertos ocupados

Si `3000` o `8001` ya están en uso, cambia `FRONTEND_HOST_PORT` o `API_HOST_PORT` en `.env` y reconstruye:

```bash
docker compose up --build -d
```

Si cambias `API_HOST_PORT`, actualiza también `NEXT_PUBLIC_API_BASE_URL` para que apunte al nuevo puerto público.

### El frontend no construye fuera del contenedor

El frontend declara soporte para Node `>=20 <23` y recomienda Node 22 LTS. El flujo soportado del proyecto es construirlo dentro de Docker, donde esa compatibilidad queda controlada por la imagen base `node:22-alpine`.

### La API no responde

Comprueba el healthcheck y revisa logs:

```bash
docker compose ps
docker compose logs -f api
```

### Errores al generar historias o ilustraciones

- Verifica que `OPENAI_API_KEY` esté presente en `.env`.
- Si el frontend carga pero falla al consumir la API, revisa `NEXT_PUBLIC_API_BASE_URL` e `INTERNAL_API_BASE_URL`.
- Si el proxy intermedio corta la respuesta, confirma que permita streaming NDJSON.
