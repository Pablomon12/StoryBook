# Creador de historias con dibujos

Aplicacion con backend `FastAPI` y frontend `Next.js` que transforma un dibujo subido por el usuario en una historia infantil ilustrada. La API analiza la imagen, genera escenas y opciones con OpenAI, y el frontend reproduce la aventura paso a paso.

## Stack

- Backend: `FastAPI`
- Frontend: `Next.js 15`
- Dependencias Python: `uv`
- Modelos OpenAI para vision, texto e imagen

## Requisitos

- Docker y Docker Compose para levantar la app completa sin instalar nada mas
- Python `3.14` o superior, `uv` y Node.js `22` solo si vas a desarrollar fuera de Docker
- Una `OPENAI_API_KEY` valida

## Variables de entorno

Para Docker Compose y backend, usa el `.env` de la raiz del proyecto:

```bash
cp .env.example .env
```

Contenido minimo:

```bash
OPENAI_API_KEY=tu_api_key_de_openai
FRONTEND_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api
INTERNAL_API_BASE_URL=http://api:8000/api
API_HOST_PORT=8001
FRONTEND_HOST_PORT=3000
```

`FRONTEND_ORIGINS` admite varios origenes separados por comas para configurar CORS, por ejemplo:

```bash
FRONTEND_ORIGINS=https://mi-frontend.com,http://localhost:3000
```

`NEXT_PUBLIC_API_BASE_URL` es la URL publica que consumira el navegador. Con Docker Compose debe apuntar a la API expuesta en tu maquina, por ejemplo `http://localhost:8001/api`.

`INTERNAL_API_BASE_URL` es la URL privada que usa el contenedor del frontend para reenviar peticiones al backend dentro de la red Docker. Por defecto es `http://api:8000/api` y no suele hacer falta tocarla.

`API_HOST_PORT` y `FRONTEND_HOST_PORT` controlan los puertos expuestos en tu maquina. Si cambias `API_HOST_PORT`, actualiza tambien `NEXT_PUBLIC_API_BASE_URL` para que use ese puerto publico real.

Si desarrollas el frontend fuera de Docker, crea tambien su archivo local:

```bash
cd frontend
cp .env.example .env.local
```

Contenido:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api
```

## Despliegue con Docker

Es la forma recomendada de ejecutar la aplicacion completa. Levanta API y frontend sin instalar `uv`, `Python`, `Node.js` ni dependencias fuera de los contenedores.

1. Crea el archivo de entorno:

```bash
cp .env.example .env
```

2. Edita `.env` y define al menos:

```bash
OPENAI_API_KEY=tu_api_key_de_openai
FRONTEND_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api
INTERNAL_API_BASE_URL=http://api:8000/api
API_HOST_PORT=8001
FRONTEND_HOST_PORT=3000
```

3. Construye y arranca todo el stack:

```bash
docker compose up --build -d
```

4. Abre la aplicacion y verifica servicios:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8001`
- Documentacion Swagger: `http://localhost:8001/docs`
- Healthcheck: `http://localhost:8001/api/health`

Comandos utiles:

```bash
docker compose logs -f
docker compose down
```

Notas operativas:

- `docker compose` levanta dos servicios: `api` y `frontend`.
- El frontend llama directamente a `NEXT_PUBLIC_API_BASE_URL` desde el navegador.
- Si el puerto `8000` o `3000` ya esta ocupado en tu maquina, cambia `API_HOST_PORT` o `FRONTEND_HOST_PORT` en `.env` y vuelve a ejecutar `docker compose up --build -d`.
- Si expones el frontend en otro dominio o puerto, `FRONTEND_ORIGINS` debe incluir ese origen para las llamadas directas que hagas fuera del proxy del frontend.
- Los endpoints `/api/stories/start` y `/api/stories/continue` devuelven `application/x-ndjson`; si pones un proxy delante, no debe cortar ni bufferizar el streaming.

## Desarrollo local

Usa este flujo solo si quieres trabajar fuera de Docker.

1. Instala dependencias del backend:

```bash
uv sync
```

2. Instala dependencias del frontend:

```bash
nvm use 22
cd frontend
npm install
```

Si no usas `nvm`, selecciona manualmente `Node 22`.

3. Arranca la API:

```bash
uv run uvicorn app.main:app --reload
```

4. Arranca el frontend:

```bash
cd frontend
npm run dev
```

URLs por defecto:

- API: `http://127.0.0.1:8000`
- Documentacion Swagger: `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/api/health`
- Frontend: `http://localhost:3000`

## Endpoints principales

- `POST /api/characters/describe`: analiza el dibujo subido.
- `POST /api/stories/start`: inicia la historia en streaming NDJSON.
- `POST /api/stories/choices`: genera dos opciones de continuacion.
- `POST /api/stories/continue`: continua la historia en streaming NDJSON.
- `POST /api/images/generate`: genera la ilustracion de una escena.
- `GET /api/health`: devuelve estado y version de la API.

## Frontend

El frontend lee la URL base de la API desde `NEXT_PUBLIC_API_BASE_URL`. En Docker Compose debe apuntar a la URL publica real de FastAPI, por ejemplo `http://localhost:8001/api`. En desarrollo local fuera de Docker puedes seguir usando `frontend/.env.local` con `http://127.0.0.1:8000/api`.

## Tests

Ejecuta los tests del backend con:

```bash
uv run pytest
```

Los tests mockean OpenAI y no deben llamar servicios externos.

## Solucion de problemas del frontend

Si `npm run dev` falla por incompatibilidad de runtime, revisa primero la version de Node:

```bash
node -v
```

Si estas fuera de `20.x`, `21.x` o `22.x`, cambia a `Node 22` y reinstala dependencias:

```bash
nvm use 22
cd frontend
rm -rf node_modules .next package-lock.json
npm install
npm run dev
```
