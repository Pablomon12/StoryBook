# Creador de historias con dibujos

Aplicacion con backend `FastAPI` y frontend `Next.js` que transforma un dibujo subido por el usuario en una historia infantil ilustrada. El repositorio esta preparado para ejecutarse exclusivamente con Docker: tanto la API como el frontend se construyen y arrancan con `docker compose`.

## Stack

- Backend: `FastAPI`
- Frontend: `Next.js 15`
- Orquestacion: `docker compose`
- Modelos OpenAI para vision, texto e imagen

## Requisitos

- Docker Engine con `docker compose`
- Una `OPENAI_API_KEY` valida

No hace falta instalar `Python`, `uv`, `Node.js` ni dependencias del proyecto en la maquina host.

## Configuracion

El despliegue usa un unico archivo `.env` en la raiz del proyecto:

```bash
cp .env.example .env
```

Variables minimas:

```bash
OPENAI_API_KEY=tu_api_key_de_openai
FRONTEND_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api
INTERNAL_API_BASE_URL=http://api:8000/api
API_HOST_PORT=8001
FRONTEND_HOST_PORT=3000
```

Consideraciones:

- `FRONTEND_ORIGINS` admite varios origenes separados por comas para configurar CORS.
- `NEXT_PUBLIC_API_BASE_URL` es la URL publica que consumira el navegador y debe apuntar al puerto publicado por la API.
- `INTERNAL_API_BASE_URL` es la URL privada entre contenedores y por defecto debe mantenerse como `http://api:8000/api`.
- `API_HOST_PORT` y `FRONTEND_HOST_PORT` controlan los puertos publicados en la maquina host.

Ejemplo de multiples origenes:

```bash
FRONTEND_ORIGINS=https://mi-frontend.com,http://localhost:3000
```

## Despliegue

1. Crea el archivo de entorno:

```bash
cp .env.example .env
```

2. Edita `.env` y define al menos `OPENAI_API_KEY`.

3. Construye y arranca el stack:

```bash
docker compose up --build -d
```

4. Verifica los servicios:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8001`
- Swagger: `http://localhost:8001/docs`
- Healthcheck: `http://localhost:8001/api/health`

## Operacion

Comandos utiles:

```bash
docker compose logs -f
docker compose ps
docker compose down
```

Notas operativas:

- `docker compose` levanta dos servicios: `api` y `frontend`.
- El frontend se construye con `NEXT_PUBLIC_API_BASE_URL` y usa `INTERNAL_API_BASE_URL` para comunicarse con la API dentro de la red Docker.
- Si cambias `API_HOST_PORT`, actualiza tambien `NEXT_PUBLIC_API_BASE_URL` para que apunte al puerto publico real.
- Si cambias `FRONTEND_HOST_PORT` o publicas el frontend en otro dominio, añade ese origen a `FRONTEND_ORIGINS`.
- Los endpoints `/api/stories/start` y `/api/stories/continue` responden en `application/x-ndjson`; cualquier proxy intermedio debe permitir streaming sin buffer.

## Endpoints principales

- `POST /api/characters/describe`: analiza el dibujo subido.
- `POST /api/stories/start`: inicia la historia en streaming NDJSON.
- `POST /api/stories/choices`: genera dos opciones de continuacion.
- `POST /api/stories/continue`: continua la historia en streaming NDJSON.
- `POST /api/images/generate`: genera la ilustracion de una escena.
- `GET /api/health`: devuelve estado y version de la API.

## Solucion de problemas

Si un puerto ya esta ocupado en la maquina host, cambia `API_HOST_PORT` o `FRONTEND_HOST_PORT` en `.env` y reconstruye:

```bash
docker compose up --build -d
```

Si necesitas revisar por que un servicio no arranca, consulta sus logs:

```bash
docker compose logs -f api
docker compose logs -f frontend
```
