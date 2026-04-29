# Creador de historias con dibujos

Aplicacion con backend `FastAPI` y frontend `Next.js` que transforma un dibujo subido por el usuario en una historia infantil ilustrada. La API analiza la imagen, genera escenas y opciones con OpenAI, y el frontend reproduce la aventura paso a paso.

## Stack

- Backend: `FastAPI`
- Frontend: `Next.js 15`
- Dependencias Python: `uv`
- Modelos OpenAI para vision, texto e imagen

## Requisitos

- Python `3.14` o superior
- `uv`
- Node.js `22` recomendado para el frontend (`>=20 <23` soportado)
- Una `OPENAI_API_KEY` valida

## Variables de entorno

Backend en la raiz del proyecto:

```bash
cp .env.example .env
```

Contenido minimo:

```bash
OPENAI_API_KEY=tu_api_key_de_openai
FRONTEND_ORIGINS=http://localhost:3000
```

`FRONTEND_ORIGINS` admite varios origenes separados por comas para configurar CORS, por ejemplo:

```bash
FRONTEND_ORIGINS=https://mi-frontend.com,http://localhost:3000
```

Frontend:

```bash
cd frontend
cp .env.example .env.local
```

Contenido:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api
```

## Desarrollo local

1. Instala dependencias del backend:

```bash
uv sync
```

2. Instala dependencias del frontend:

```bash
nvm use
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

## Despliegue de la API

La API se puede desplegar en cualquier plataforma que permita ejecutar un proceso Python persistente, por ejemplo Railway, Render, Fly.io o un VPS.

### 1. Preparar el entorno

- Usa Python `3.14`.
- Instala dependencias con `uv sync --frozen`.
- Define al menos estas variables:
  - `OPENAI_API_KEY`
  - `FRONTEND_ORIGINS`

### 2. Comando de arranque

Ejecuta `uvicorn` escuchando en todas las interfaces:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Si la plataforma inyecta un puerto concreto, adapta el comando a ese valor.

### 3. Configurar CORS

`FRONTEND_ORIGINS` debe contener la URL publica del frontend. Ejemplo:

```bash
FRONTEND_ORIGINS=https://story-creator.vercel.app
```

Si mantienes entorno local y produccion:

```bash
FRONTEND_ORIGINS=https://story-creator.vercel.app,http://localhost:3000
```

### 4. Verificar el despliegue

Comprueba que estos endpoints responden:

- `GET /api/health`
- `POST /api/characters/describe`
- `POST /api/stories/start`
- `POST /api/stories/choices`
- `POST /api/stories/continue`
- `POST /api/images/generate`

Los endpoints `/api/stories/start` y `/api/stories/continue` devuelven `application/x-ndjson`, así que el proxy o plataforma no debe romper respuestas en streaming.

## Endpoints principales

- `POST /api/characters/describe`: analiza el dibujo subido.
- `POST /api/stories/start`: inicia la historia en streaming NDJSON.
- `POST /api/stories/choices`: genera dos opciones de continuacion.
- `POST /api/stories/continue`: continua la historia en streaming NDJSON.
- `POST /api/images/generate`: genera la ilustracion de una escena.
- `GET /api/health`: devuelve estado y version de la API.

## Frontend

El frontend lee la URL base de la API desde `NEXT_PUBLIC_API_BASE_URL`. Si despliegas la API en otra URL, actualiza `frontend/.env.local` en desarrollo o la variable publica equivalente en produccion.

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
nvm use
cd frontend
rm -rf node_modules .next package-lock.json
npm install
npm run dev
```
