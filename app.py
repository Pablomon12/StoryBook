import streamlit as st
from PIL import Image

from app.api.character import extract_drawing_description, generate_character_image
from app.api.story import continue_written_story, generate_story_choices, start_written_story
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


st.set_page_config(page_title="Creador de historias")


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
    if "story_choices" not in st.session_state:
        st.session_state.story_choices = []
    if "selected_choice" not in st.session_state:
        st.session_state.selected_choice = ""
    if "last_selected_choice" not in st.session_state:
        st.session_state.last_selected_choice = ""
    if "story_state" not in st.session_state:
        st.session_state.story_state = create_initial_state()


def start_story(uploaded_file) -> None:
    character_name = st.session_state.character_name
    character_personality = st.session_state.character_personality
    situation_description = st.session_state.situation_description

    with st.spinner("Analizando dibujo..."):
        st.session_state.drawing_description = extract_drawing_description(
            uploaded_image=uploaded_file,
            character_name=character_name,
            character_personality=character_personality,
        )

    with st.spinner("Generando imagen..."):
        st.session_state.generated_image = generate_character_image(
            character_name=character_name,
            character_personality=character_personality,
            drawing_description=st.session_state.drawing_description,
            situation_description=situation_description,
        )
        st.session_state.story_images = [
            {
                "image": st.session_state.generated_image,
                "caption": "Inicio de la historia",
            }
        ]

    with st.spinner("Escribiendo inicio de la historia..."):
        st.session_state.story_text = start_written_story(
            character_name=character_name,
            character_personality=character_personality,
            drawing_description=st.session_state.drawing_description,
            situation_description=situation_description,
        )

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
    story_state = register_generated_image(story_state)
    story_state = add_story_text(story_state, st.session_state.story_text)
    st.session_state.story_state = move_to_next_checkpoint(story_state)
    st.session_state.selected_choice = ""
    st.session_state.last_selected_choice = ""
    st.session_state.story_started = True


def choose_story_option(choice: str) -> None:
    st.session_state.selected_choice = choice
    st.session_state.last_selected_choice = choice

    story_state = register_choice(st.session_state.story_state, choice)
    is_ending = story_state.phase == StoryPhase.ENDING

    with st.spinner("Continuando la historia..."):
        new_story_text = continue_written_story(
            story_text=st.session_state.story_text,
            selected_choice=choice,
            character_name=st.session_state.character_name,
            character_personality=st.session_state.character_personality,
            is_ending=is_ending,
        )

    if can_generate_image(story_state):
        with st.spinner("Generando nueva imagen con tu eleccion..."):
            st.session_state.generated_image = generate_character_image(
                character_name=st.session_state.character_name,
                character_personality=st.session_state.character_personality,
                drawing_description=st.session_state.drawing_description,
                situation_description=st.session_state.situation_description,
                story_context=st.session_state.story_text,
                chosen_action=choice,
            )
            st.session_state.story_images.append(
                {
                    "image": st.session_state.generated_image,
                    "caption": choice,
                }
            )
            story_state = register_generated_image(story_state)

    st.session_state.story_text = f"{st.session_state.story_text}\n\n{new_story_text}"
    story_state = add_story_text(story_state, new_story_text)
    story_state = move_to_next_checkpoint(story_state)
    st.session_state.story_state = story_state

    if is_finished(story_state):
        st.session_state.story_choices = []
        return

    with st.spinner("Preparando nuevas opciones..."):
        st.session_state.story_choices = generate_story_choices(
            story_text=st.session_state.story_text,
            character_name=st.session_state.character_name,
            character_personality=st.session_state.character_personality,
        )
    st.session_state.selected_choice = ""


def main() -> None:
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

    start_disabled = uploaded_file is None
    if st.button("Comenzar historia", disabled=start_disabled, type="primary"):
        start_story(uploaded_file)

    st.divider()
    st.subheader("Estado de sesión")
    st.write(
        {
            "historia_comenzada": st.session_state.story_started,
            "imagen_cargada": st.session_state.uploaded_image_name,
            "nombre_personaje": character_name,
            "personalidad": character_personality,
            "situacion": situation_description,
            "descripcion_dibujo": st.session_state.drawing_description,
            "texto_historia": st.session_state.story_text,
            "opciones": st.session_state.story_choices,
            "opcion_elegida": st.session_state.last_selected_choice,
        }
    )

    if st.session_state.story_started:
        st.success("La historia ha comenzado.")
        image_column, story_column = st.columns(2)

        with image_column:
            if st.session_state.story_images:
                st.subheader("Imagenes de la historia")
                for story_image in st.session_state.story_images:
                    st.image(
                        story_image["image"],
                        caption=story_image["caption"],
                        use_container_width=True,
                    )

        with story_column:
            if st.session_state.story_text:
                st.subheader("Inicio de la historia")
                st.write(st.session_state.story_text)

                if st.session_state.story_choices:
                    st.subheader("Como quieres continuar?")
                    choice_columns = st.columns(2)
                    for index, choice in enumerate(st.session_state.story_choices):
                        with choice_columns[index]:
                            st.button(
                                choice,
                                key=f"story_choice_{index}",
                                disabled=bool(st.session_state.selected_choice),
                                use_container_width=True,
                                on_click=choose_story_option,
                                args=(choice,),
                            )

                if st.session_state.last_selected_choice:
                    st.info(f"Ultima eleccion: {st.session_state.last_selected_choice}")


if __name__ == "__main__":
    main()
