# Creador de historias con dibujos

Aplicacion en Streamlit que transforma un dibujo subido por el usuario en una historia infantil ilustrada. La app analiza el dibujo con OpenAI, genera una imagen del personaje, escribe el inicio de la historia y permite continuarla mediante opciones interactivas.

## Requisitos

- Python 3.14 o superior.
- `uv` instalado para gestionar dependencias y ejecutar comandos.
- Una API key de OpenAI.


Puedes comprobar las versiones con:

```bash
python --version
uv --version
```

## Configuracion local

1. Clona el repositorio y entra en la carpeta del proyecto:

```bash
git clone <URL_DEL_REPOSITORIO>
cd CHALLENGE
```

2. Instala las dependencias:

```bash
uv sync
```

3. Crea el archivo de variables de entorno:

```bash
cp .env.example .env
```

4. Edita `.env` y reemplaza el valor de ejemplo por tu API key real:

```bash
OPENAI_API_KEY=tu_api_key_de_openai
```

No subas `.env` al repositorio. Ese archivo contiene credenciales privadas.

## Levantar la app en local

Ejecuta Streamlit desde la raiz del proyecto:

```bash
uv run streamlit run app.py
```

Cuando el servidor arranque, Streamlit mostrara una URL local similar a:

```text
http://localhost:8501
```

Abre esa URL en el navegador para usar la aplicacion.

## Flujo de uso

1. Sube una imagen del dibujo del personaje.
2. Escribe el nombre del personaje.
3. Describe su personalidad.
4. Indica la situacion o entorno inicial.
5. Pulsa `Comenzar historia`.
6. Elige una de las opciones para continuar la aventura.

La app generara nuevas partes de la historia y nuevas imagenes segun la opcion elegida.

## Comandos utiles

Ejecutar la app:

```bash
uv run streamlit run app.py
```

Ejecutar el punto de entrada basico:

```bash
uv run python main.py
```

Ejecutar los tests:

```bash
uv run pytest
```

Verificar sintaxis de los modulos principales:

```bash
uv run python -m py_compile app.py app/api/story.py app/api/character.py app/models/story_engine.py
```

## Estructura del proyecto

```text
.
├── app.py                    # Entrada principal de Streamlit
├── app/
│   ├── api/
│   │   ├── character.py      # Analisis del dibujo y generacion de imagenes
│   │   └── story.py          # Generacion y continuacion de historias
│   ├── core/
│   │   ├── agent.py          # Configuracion de agentes/modelos OpenAI
│   │   └── config.py         # Lectura de variables de entorno
│   ├── models/
│   │   └── story_engine.py   # Logica de fases y estado de la historia
│   └── story.py              # Modelos de dominio
├── tests/                    # Tests automatizados
├── pyproject.toml            # Dependencias y configuracion del proyecto
├── uv.lock                   # Lockfile de dependencias
└── .env.example              # Variables de entorno de ejemplo
```

## Variables de entorno

| Variable | Descripcion | Obligatoria |
| --- | --- | --- |
| `OPENAI_API_KEY` | API key usada para llamar a los modelos de OpenAI. | Si |

## Solucion de problemas

Si `uv run streamlit run app.py` falla porque falta la API key, revisa que exista `.env` y que contenga `OPENAI_API_KEY`.

Si el navegador no abre automaticamente, copia la URL que muestra Streamlit en la terminal y pegala manualmente en el navegador.

Si las dependencias no se instalan correctamente, vuelve a sincronizar el entorno:

```bash
uv sync
```
# StoryBook
