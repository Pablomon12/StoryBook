from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import streamlit as st
from PIL import Image

from app.api.character import extract_drawing_description, generate_character_image
from app.api.story import generate_story_choices, stream_continue_written_story, stream_start_written_story
from app.models.story_engine import (
    add_story_text,
    can_generate_image,
    create_initial_state,
    is_finished,
    move_to_next_checkpoint,
    register_generated_image,
    register_choice,
    set_character,
)
from app.story import CharacterProfile, StoryPhase


def append_story_text(existing_text: str, new_text: str) -> str:
    base = existing_text.strip()
    addition = new_text.strip()
    if not base:
        return addition
    if not addition:
        return base
    return f"{base}\n\n{addition}"


def split_story_text(story_text: str, current_scene_text: str) -> tuple[str, str]:
    full_story = story_text.strip()
    current_scene = current_scene_text.strip()

    if not current_scene:
        return full_story, ""

    if full_story.endswith(current_scene):
        history = full_story[: -len(current_scene)].rstrip()
        return history, current_scene

    return full_story, current_scene


def collect_streamed_text(
    chunks: Iterable[Any],
    on_update: Callable[[str, bool], None] | None = None,
) -> str:
    parts: list[str] = []

    for chunk in chunks:
        parts.append(str(chunk))
        if on_update is not None:
            on_update("".join(parts), True)

    final_text = "".join(parts).strip()
    if on_update is not None:
        on_update(final_text, False)

    return final_text


def stream_text_into_placeholder(chunks: Iterable[Any], placeholder: Any) -> str:
    def render(text: str, is_streaming: bool) -> None:
        content = text or "_Escribiendo..._"
        if is_streaming and text:
            content = f"{text}▌"
        placeholder.markdown(content)

    return collect_streamed_text(chunks, on_update=render)


def init_session_state() -> None:
    if "story_started" not in st.session_state:
        st.session_state.story_started = False
    if "uploaded_image_name" not in st.session_state:
        st.session_state.uploaded_image_name = None
    if "character_name" not in st.session_state:
        st.session_state.character_name = ""
    if "character_personality" not in st.session_state:
        st.session_state.character_personality = ""
    if "situation_description" not in st.session_state:
        st.session_state.situation_description = ""
    if "drawing_description" not in st.session_state:
        st.session_state.drawing_description = ""
    if "generated_image" not in st.session_state:
        st.session_state.generated_image = None
    if "story_images" not in st.session_state:
        st.session_state.story_images = []
    if "story_text" not in st.session_state:
        st.session_state.story_text = ""
    if "current_scene_text" not in st.session_state:
        st.session_state.current_scene_text = ""
    if "story_choices" not in st.session_state:
        st.session_state.story_choices = []
    if "selected_choice" not in st.session_state:
        st.session_state.selected_choice = ""
    if "last_selected_choice" not in st.session_state:
        st.session_state.last_selected_choice = ""
    if "story_state" not in st.session_state:
        st.session_state.story_state = create_initial_state()
    if "is_generating_story" not in st.session_state:
        st.session_state.is_generating_story = False
    if "is_generating_image" not in st.session_state:
        st.session_state.is_generating_image = False
    if "pending_image_caption" not in st.session_state:
        st.session_state.pending_image_caption = ""


def render_story_workspace() -> dict[str, Any]:
    image_column, story_column = st.columns([1, 1.2], gap="large")

    with image_column:
        current_image_placeholder = st.empty()
        image_history_placeholder = st.empty()

    with story_column:
        story_history_placeholder = st.empty()
        current_scene_placeholder = st.empty()
        choices_placeholder = st.empty()
        last_choice_placeholder = st.empty()

    return {
        "current_image": current_image_placeholder,
        "image_history": image_history_placeholder,
        "story_history": story_history_placeholder,
        "current_scene": current_scene_placeholder,
        "choices": choices_placeholder,
        "last_choice": last_choice_placeholder,
    }


def render_image_section(workspace: dict[str, Any]) -> None:
    current_image_placeholder = workspace["current_image"]
    image_history_placeholder = workspace["image_history"]

    with current_image_placeholder.container():
        st.subheader("Ilustracion actual")
        if st.session_state.is_generating_image:
            caption = st.session_state.pending_image_caption or "Preparando ilustracion..."
            st.info(caption)
        elif st.session_state.story_images:
            latest_image = st.session_state.story_images[-1]
            st.image(
                latest_image["image"],
                caption=latest_image["caption"],
                use_container_width=True,
            )
        else:
            st.info("La ilustracion aparecera aqui.")

    with image_history_placeholder.container():
        previous_images = st.session_state.story_images[:-1]
        if previous_images:
            st.subheader("Imagenes anteriores")
            for story_image in previous_images:
                st.image(
                    story_image["image"],
                    caption=story_image["caption"],
                    use_container_width=True,
                )


def render_story_section(workspace: dict[str, Any]) -> None:
    story_history_placeholder = workspace["story_history"]
    current_scene_placeholder = workspace["current_scene"]
    last_choice_placeholder = workspace["last_choice"]

    history_text, current_scene_text = split_story_text(
        st.session_state.story_text,
        st.session_state.current_scene_text,
    )

    with story_history_placeholder.container():
        st.subheader("Historia")
        if history_text:
            st.markdown(history_text)
        elif st.session_state.story_started or st.session_state.is_generating_story:
            st.caption("La aventura esta comenzando...")
        else:
            st.caption("El texto de la historia aparecera aqui.")

    with current_scene_placeholder.container():
        if current_scene_text or st.session_state.is_generating_story:
            st.subheader("Escena actual")
            if st.session_state.last_selected_choice:
                st.caption(f"Eleccion: {st.session_state.last_selected_choice}")
            text_placeholder = st.empty()
            if current_scene_text:
                text_placeholder.markdown(current_scene_text)
            else:
                text_placeholder.markdown("_Escribiendo..._")
        else:
            current_scene_placeholder.empty()

    if st.session_state.last_selected_choice and not current_scene_text:
        last_choice_placeholder.info(f"Ultima eleccion: {st.session_state.last_selected_choice}")
    else:
        last_choice_placeholder.empty()


def render_story_workspace_state(workspace: dict[str, Any]) -> None:
    render_image_section(workspace)
    render_story_section(workspace)


def render_story_choices(workspace: dict[str, Any]) -> str | None:
    if not st.session_state.story_choices:
        workspace["choices"].empty()
        return None

    with workspace["choices"].container():
        st.subheader("Como quieres continuar?")
        choice_columns = st.columns(2)
        for index, choice in enumerate(st.session_state.story_choices):
            with choice_columns[index]:
                if st.button(
                    choice,
                    key=f"story_choice_{index}",
                    disabled=st.session_state.is_generating_story or st.session_state.is_generating_image,
                    use_container_width=True,
                ):
                    return choice

    return None


def run_story_turn(
    workspace: dict[str, Any],
    story_chunks: Iterable[Any],
    image_kwargs: dict[str, Any] | None,
    image_caption: str,
) -> tuple[str, bytes | None]:
    current_scene_placeholder = workspace["current_scene"]
    workspace["choices"].empty()

    st.session_state.current_scene_text = ""
    st.session_state.pending_image_caption = image_caption
    st.session_state.is_generating_story = True
    st.session_state.is_generating_image = image_kwargs is not None
    render_story_workspace_state(workspace)

    image_future = None
    if image_kwargs is not None:
        executor = ThreadPoolExecutor(max_workers=1)
        image_future = executor.submit(generate_character_image, **image_kwargs)
    else:
        executor = None

    try:
        with current_scene_placeholder.container():
            st.subheader("Escena actual")
            if st.session_state.last_selected_choice:
                st.caption(f"Eleccion: {st.session_state.last_selected_choice}")
            live_text_placeholder = st.empty()
            streamed_text = stream_text_into_placeholder(story_chunks, live_text_placeholder)

        st.session_state.current_scene_text = streamed_text
        st.session_state.is_generating_story = False
        render_story_workspace_state(workspace)

        generated_image = image_future.result() if image_future is not None else None
    finally:
        if image_future is not None:
            executor.shutdown(wait=True)

    st.session_state.is_generating_image = False
    st.session_state.pending_image_caption = ""
    render_story_workspace_state(workspace)

    return st.session_state.current_scene_text, generated_image


def start_story(uploaded_file, workspace: dict[str, Any]) -> None:
    character_name = st.session_state.character_name
    character_personality = st.session_state.character_personality
    situation_description = st.session_state.situation_description

    with st.spinner("Analizando dibujo..."):
        st.session_state.drawing_description = extract_drawing_description(
            uploaded_image=uploaded_file,
            character_name=character_name,
            character_personality=character_personality,
        )

    story_text, generated_image = run_story_turn(
        workspace=workspace,
        story_chunks=stream_start_written_story(
            character_name=character_name,
            character_personality=character_personality,
            drawing_description=st.session_state.drawing_description,
            situation_description=situation_description,
        ),
        image_kwargs={
            "character_name": character_name,
            "character_personality": character_personality,
            "drawing_description": st.session_state.drawing_description,
            "situation_description": situation_description,
        },
        image_caption="Inicio de la historia",
    )

    st.session_state.story_text = story_text
    if generated_image is not None:
        st.session_state.generated_image = generated_image
        st.session_state.story_images = [
            {
                "image": generated_image,
                "caption": "Inicio de la historia",
            }
        ]

    with st.spinner("Preparando opciones..."):
        st.session_state.story_choices = generate_story_choices(
            story_text=st.session_state.story_text,
            character_name=character_name,
            character_personality=character_personality,
        )

    character = CharacterProfile(
        name=character_name,
        description=st.session_state.drawing_description,
        personality=character_personality,
    )
    story_state = set_character(create_initial_state(), character)
    if generated_image is not None:
        story_state = register_generated_image(story_state)
    story_state = add_story_text(story_state, st.session_state.story_text)
    st.session_state.story_state = move_to_next_checkpoint(story_state)
    st.session_state.selected_choice = ""
    st.session_state.last_selected_choice = ""
    st.session_state.story_started = True
    render_story_workspace_state(workspace)


def choose_story_option(choice: str, workspace: dict[str, Any]) -> None:
    st.session_state.selected_choice = choice
    st.session_state.last_selected_choice = choice

    story_state = register_choice(st.session_state.story_state, choice)
    is_ending = story_state.phase == StoryPhase.ENDING

    image_kwargs = None
    if can_generate_image(story_state):
        image_kwargs = {
            "character_name": st.session_state.character_name,
            "character_personality": st.session_state.character_personality,
            "drawing_description": st.session_state.drawing_description,
            "situation_description": st.session_state.situation_description,
            "story_context": st.session_state.story_text,
            "chosen_action": choice,
        }

    new_story_text, generated_image = run_story_turn(
        workspace=workspace,
        story_chunks=stream_continue_written_story(
            story_text=st.session_state.story_text,
            selected_choice=choice,
            character_name=st.session_state.character_name,
            character_personality=st.session_state.character_personality,
            is_ending=is_ending,
        ),
        image_kwargs=image_kwargs,
        image_caption=choice,
    )

    if generated_image is not None:
        st.session_state.generated_image = generated_image
        st.session_state.story_images.append(
            {
                "image": generated_image,
                "caption": choice,
            }
        )
        story_state = register_generated_image(story_state)

    st.session_state.story_text = append_story_text(st.session_state.story_text, new_story_text)
    story_state = add_story_text(story_state, new_story_text)
    story_state = move_to_next_checkpoint(story_state)
    st.session_state.story_state = story_state

    if is_finished(story_state):
        st.session_state.story_choices = []
        st.session_state.selected_choice = ""
        render_story_workspace_state(workspace)
        return

    with st.spinner("Preparando nuevas opciones..."):
        st.session_state.story_choices = generate_story_choices(
            story_text=st.session_state.story_text,
            character_name=st.session_state.character_name,
            character_personality=st.session_state.character_personality,
        )

    st.session_state.selected_choice = ""
    render_story_workspace_state(workspace)


def main() -> None:
    st.set_page_config(page_title="Creador de historias")
    init_session_state()

    st.title("Creador de historias con dibujos")

    uploaded_file = st.file_uploader(
        "Sube una imagen de tu dibujo",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False,
    )
    character_name = st.text_input(
        "Nombre del personaje",
        max_chars=30,
        placeholder="Ej: Luna",
        key="character_name",
    )
    character_personality = st.text_input(
        "Describe la personalidad del personaje",
        max_chars=50,
        placeholder="Ej: valiente, curioso y divertido",
        key="character_personality",
    )
    situation_description = st.text_area(
        "Describe la situacion o entorno",
        placeholder="Ej: caminando por un bosque magico al atardecer",
        key="situation_description",
    )

    if uploaded_file is not None:
        st.session_state.uploaded_image_name = uploaded_file.name
        image = Image.open(uploaded_file)

        st.subheader("Preview del dibujo")
        st.image(image, caption=uploaded_file.name, use_container_width=True)
    else:
        st.info("Sube un dibujo para ver la preview antes de comenzar.")

    start_requested = st.button(
        "Comenzar historia",
        disabled=uploaded_file is None or st.session_state.is_generating_story or st.session_state.is_generating_image,
        type="primary",
    )

    should_show_workspace = st.session_state.story_started or start_requested
    workspace = None

    if should_show_workspace:
        st.divider()
        st.success("La historia ha comenzado.")
        workspace = render_story_workspace()
        render_story_workspace_state(workspace)

    if start_requested and workspace is not None:
        start_story(uploaded_file, workspace)

    if st.session_state.story_started and workspace is not None:
        render_story_workspace_state(workspace)
        selected_choice = render_story_choices(workspace)
        if selected_choice:
            choose_story_option(selected_choice, workspace)
            st.rerun()

    with st.expander("Estado de sesión", expanded=False):
        st.write(
            {
                "historia_comenzada": st.session_state.story_started,
                "imagen_cargada": st.session_state.uploaded_image_name,
                "nombre_personaje": character_name,
                "personalidad": character_personality,
                "situacion": situation_description,
                "descripcion_dibujo": st.session_state.drawing_description,
                "texto_historia": st.session_state.story_text,
                "escena_actual": st.session_state.current_scene_text,
                "opciones": st.session_state.story_choices,
                "opcion_elegida": st.session_state.last_selected_choice,
            }
        )


if __name__ == "__main__":
    main()
