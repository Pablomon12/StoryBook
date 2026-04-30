"use client";

import { ChangeEvent, FormEvent, useState } from "react";

type StoryPhase =
  | "start"
  | "opening"
  | "choice_1"
  | "continuation"
  | "choice_2"
  | "ending"
  | "finished";

type StoryState = {
  phase: StoryPhase;
  choices: string[];
  image_count: number;
  max_images: number;
};

type StoryDoneEvent = {
  type: "done";
  story_text: string;
  current_scene_text: string;
  story_state: StoryState;
  is_finished: boolean;
  can_generate_image: boolean;
};

type StoryImage = {
  caption: string;
  src: string;
};

type ErrorPayload = {
  detail?: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";
const EMPTY_STATE: StoryState = {
  phase: "start",
  choices: [],
  image_count: 0,
  max_images: 3,
};

function incrementImageCount(state: StoryState): StoryState {
  return {
    ...state,
    image_count: Math.min(state.image_count + 1, state.max_images),
  };
}

async function parseStoryStream(
  response: Response,
  onDelta: (text: string) => void,
): Promise<StoryDoneEvent> {
  if (!response.ok || !response.body) {
    throw new Error("No se pudo leer la respuesta del servidor.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentText = "";
  let donePayload: StoryDoneEvent | null = null;

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line) {
        continue;
      }

      const event = JSON.parse(line) as { type: string; text?: string } | StoryDoneEvent;
      if (event.type === "delta" && "text" in event && typeof event.text === "string") {
        currentText += event.text;
        onDelta(currentText);
      }
      if (event.type === "done") {
        donePayload = event as StoryDoneEvent;
      }
    }

    if (done) {
      break;
    }
  }

  if (!donePayload) {
    throw new Error("La historia no termino correctamente.");
  }

  return donePayload;
}

async function generateChoices(storyText: string, characterName: string, characterPersonality: string) {
  const response = await fetch(`${API_BASE_URL}/stories/choices`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      story_text: storyText,
      character_name: characterName,
      character_personality: characterPersonality,
    }),
  });

  if (!response.ok) {
    throw new Error("No se pudieron generar nuevas opciones.");
  }

  const payload = (await response.json()) as { choices: string[] };
  return payload.choices;
}

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>("");
  const [characterName, setCharacterName] = useState("");
  const [characterPersonality, setCharacterPersonality] = useState("");
  const [situationDescription, setSituationDescription] = useState("");
  const [drawingDescription, setDrawingDescription] = useState("");
  const [storyText, setStoryText] = useState("");
  const [currentSceneText, setCurrentSceneText] = useState("");
  const [choices, setChoices] = useState<string[]>([]);
  const [storyState, setStoryState] = useState<StoryState>(EMPTY_STATE);
  const [storyImages, setStoryImages] = useState<StoryImage[]>([]);
  const [lastChoice, setLastChoice] = useState("");
  const [statusMessage, setStatusMessage] = useState("Sube un dibujo para comenzar la aventura.");
  const [isStarting, setIsStarting] = useState(false);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [isChoosing, setIsChoosing] = useState(false);

  const isBusy = isStarting || isGeneratingImage || isChoosing;

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const nextFile = event.target.files?.[0] ?? null;
    setFile(nextFile);
    setPreviewUrl(nextFile ? URL.createObjectURL(nextFile) : "");
  }

  async function requestIllustration(
    nextStoryState: StoryState,
    nextDrawingDescription: string,
    storyContext: string,
    chosenAction: string,
    sceneLabel: string,
  ): Promise<StoryState> {
    if (nextStoryState.image_count >= nextStoryState.max_images) {
      return nextStoryState;
    }

    setIsGeneratingImage(true);
    setStatusMessage("Generando la ilustracion de la escena...");

    try {
      const response = await fetch(`${API_BASE_URL}/images/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          character_name: characterName,
          character_personality: characterPersonality,
          drawing_description: nextDrawingDescription,
          situation_description: situationDescription,
          story_context: storyContext,
          chosen_action: chosenAction,
        }),
      });

      if (!response.ok) {
        let errorMessage = "No se pudo crear la ilustracion.";
        try {
          const errorPayload = (await response.json()) as ErrorPayload;
          if (typeof errorPayload.detail === "string" && errorPayload.detail.trim()) {
            errorMessage = errorPayload.detail.trim();
          }
        } catch {
          // Keep the fallback message when the API returns no JSON body.
        }
        throw new Error(errorMessage);
      }

      const payload = (await response.json()) as { image_base64: string; media_type: string };
      setStoryImages((current) => [
        ...current,
        {
          caption: sceneLabel,
          src: `data:${payload.media_type};base64,${payload.image_base64}`,
        },
      ]);
      return incrementImageCount(nextStoryState);
    } finally {
      setIsGeneratingImage(false);
    }
  }

  async function handleStart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      return;
    }

    setIsStarting(true);
    setChoices([]);
    setStoryImages([]);
    setStoryText("");
    setCurrentSceneText("");
    setLastChoice("");
    setStoryState(EMPTY_STATE);
    setStatusMessage("Analizando el dibujo...");

    try {
      const describeBody = new FormData();
      describeBody.append("image", file);
      describeBody.append("character_name", characterName);
      describeBody.append("character_personality", characterPersonality);

      const describeResponse = await fetch(`${API_BASE_URL}/characters/describe`, {
        method: "POST",
        body: describeBody,
      });

      if (!describeResponse.ok) {
        throw new Error("No se pudo analizar el dibujo.");
      }

      const describePayload = (await describeResponse.json()) as { drawing_description: string };
      setDrawingDescription(describePayload.drawing_description);
      setStatusMessage("Escribiendo el inicio de la historia...");

      const startResponse = await fetch(`${API_BASE_URL}/stories/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          character_name: characterName,
          character_personality: characterPersonality,
          drawing_description: describePayload.drawing_description,
          situation_description: situationDescription,
        }),
      });

      const doneEvent = await parseStoryStream(startResponse, setCurrentSceneText);
      setStoryText(doneEvent.story_text);
      setCurrentSceneText(doneEvent.current_scene_text);

      let nextStoryState = doneEvent.story_state;
      if (doneEvent.can_generate_image) {
        nextStoryState = await requestIllustration(
          nextStoryState,
          describePayload.drawing_description,
          doneEvent.story_text,
          "",
          "Inicio de la historia",
        );
      }

      setStoryState(nextStoryState);
      setStatusMessage("Preparando opciones para continuar...");
      const nextChoices = await generateChoices(
        doneEvent.story_text,
        characterName,
        characterPersonality,
      );
      setChoices(nextChoices);
      setStatusMessage("La historia ha comenzado.");
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "La historia no pudo comenzar.");
    } finally {
      setIsStarting(false);
    }
  }

  async function handleChoice(choice: string) {
    setIsChoosing(true);
    setLastChoice(choice);
    setChoices([]);
    setStatusMessage("La aventura continua...");

    try {
      const response = await fetch(`${API_BASE_URL}/stories/continue`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          story_text: storyText,
          selected_choice: choice,
          character_name: characterName,
          character_personality: characterPersonality,
          story_state: storyState,
        }),
      });

      const doneEvent = await parseStoryStream(response, setCurrentSceneText);
      setStoryText(doneEvent.story_text);
      setCurrentSceneText(doneEvent.current_scene_text);

      let nextStoryState = doneEvent.story_state;
      if (doneEvent.can_generate_image) {
        nextStoryState = await requestIllustration(
          nextStoryState,
          drawingDescription,
          doneEvent.story_text,
          choice,
          choice,
        );
      }

      setStoryState(nextStoryState);

      if (doneEvent.is_finished) {
        setStatusMessage("La historia ha terminado con un final tierno.");
        return;
      }

      setStatusMessage("Preparando nuevas opciones...");
      const nextChoices = await generateChoices(
        doneEvent.story_text,
        characterName,
        characterPersonality,
      );
      setChoices(nextChoices);
      setStatusMessage("Elige como quieres continuar.");
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "No se pudo continuar la historia.");
    } finally {
      setIsChoosing(false);
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="pill">FastAPI + Next.js</p>
        <h1>Creador de historias con dibujos</h1>
        <p>
          Sube un dibujo, describe a tu protagonista y deja que la aventura se escriba
          escena a escena con nuevas ilustraciones.
        </p>
      </section>

      <section className="layout">
        <aside className="panel">
          <form onSubmit={handleStart}>
            <div className="field-group">
              <div className="field">
                <label htmlFor="drawing">Sube una imagen del dibujo</label>
                <input
                  id="drawing"
                  type="file"
                  accept="image/png,image/jpeg,image/jpg"
                  onChange={handleFileChange}
                />
              </div>

              <div className="field">
                <label htmlFor="name">Nombre del personaje</label>
                <input
                  id="name"
                  maxLength={30}
                  placeholder="Ej: Luna"
                  value={characterName}
                  onChange={(event) => setCharacterName(event.target.value)}
                />
              </div>

              <div className="field">
                <label htmlFor="personality">Personalidad del personaje</label>
                <input
                  id="personality"
                  maxLength={80}
                  placeholder="Ej: valiente, curiosa y divertida"
                  value={characterPersonality}
                  onChange={(event) => setCharacterPersonality(event.target.value)}
                />
              </div>

              <div className="field">
                <label htmlFor="situation">Situacion o entorno inicial</label>
                <textarea
                  id="situation"
                  rows={4}
                  placeholder="Ej: caminando por un bosque magico al atardecer"
                  value={situationDescription}
                  onChange={(event) => setSituationDescription(event.target.value)}
                />
              </div>
            </div>

            <button className="primary" type="submit" disabled={!file || isBusy}>
              {isStarting ? "Creando historia..." : "Comenzar historia"}
            </button>
          </form>

          {previewUrl ? (
            <div className="card" style={{ marginTop: "1rem" }}>
              <h3>Preview del dibujo</h3>
              <img className="preview" src={previewUrl} alt="Preview del dibujo" />
            </div>
          ) : (
            <p className="subtle">Sube un dibujo para ver la preview antes de comenzar.</p>
          )}
        </aside>

        <section className="workspace">
          <p className="status">{statusMessage}</p>

          <div className="content-grid">
            <div className="images">
              <article className="card">
                <h2>Ilustraciones</h2>
                {storyImages.length === 0 ? (
                  <p className="subtle">Las imagenes de la aventura apareceran aqui.</p>
                ) : (
                  <div className="image-stack">
                    {storyImages.map((image) => (
                      <figure key={`${image.caption}-${image.src.slice(-12)}`}>
                        <img className="story-image" src={image.src} alt={image.caption} />
                        <figcaption>{image.caption}</figcaption>
                      </figure>
                    ))}
                  </div>
                )}
              </article>
            </div>

            <div className="story">
              <article className="card">
                <h2>Historia</h2>
                {storyText ? (
                  <p className="story-copy">{storyText}</p>
                ) : (
                  <p className="subtle">El texto de la historia aparecera aqui.</p>
                )}
              </article>

              <article className="card">
                <h3>Escena actual</h3>
                {lastChoice ? <p className="pill">Eleccion: {lastChoice}</p> : null}
                <p className="story-copy">
                  {currentSceneText || "La escena actual aparecera mientras se genera la historia."}
                </p>
              </article>

              {drawingDescription ? (
                <article className="card">
                  <h3>Descripcion del dibujo</h3>
                  <p className="story-copy">{drawingDescription}</p>
                </article>
              ) : null}

              <article className="card">
                <h3>Como quieres continuar?</h3>
                {choices.length === 0 ? (
                  <p className="subtle">
                    {storyState.phase === "finished"
                      ? "La historia ya termino."
                      : "Las opciones apareceran al completar la escena actual."}
                  </p>
                ) : (
                  <div className="choices">
                    {choices.map((choice) => (
                      <button
                        key={choice}
                        className="choice-button"
                        type="button"
                        disabled={isBusy}
                        onClick={() => void handleChoice(choice)}
                      >
                        {choice}
                      </button>
                    ))}
                  </div>
                )}
              </article>
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}
