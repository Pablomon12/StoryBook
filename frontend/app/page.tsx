"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

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

type ErrorPayload = {
  detail?: string | Array<{ msg?: string }>;
};

type AppMode = "setup" | "reader";

type BookPage = {
  id: number;
  phase: StoryPhase;
  title: string;
  text: string;
  imageSrc: string;
  choiceUsed: string;
  selectedChoice: string;
  isGeneratingText: boolean;
  isGeneratingImage: boolean;
  isComplete: boolean;
  choices: string[];
};

const PUBLIC_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const EMPTY_STATE: StoryState = {
  phase: "start",
  choices: [],
  image_count: 0,
  max_images: 3,
};
const IMAGE_STORY_CONTEXT_LIMIT = 5000;

function incrementImageCount(state: StoryState): StoryState {
  return {
    ...state,
    image_count: Math.min(state.image_count + 1, state.max_images),
  };
}

function clampText(value: string, maxLength: number): string {
  if (value.length <= maxLength) {
    return value;
  }

  return value.slice(0, maxLength);
}

function resolveApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return "/api";
  }

  const hostname = window.location.hostname;
  const isLocalhost =
    hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";

  if (isLocalhost && PUBLIC_API_BASE_URL) {
    return PUBLIC_API_BASE_URL;
  }

  return "/api";
}

function getErrorMessage(payload: ErrorPayload, fallback: string): string {
  if (typeof payload.detail === "string" && payload.detail.trim()) {
    return payload.detail.trim();
  }

  if (Array.isArray(payload.detail)) {
    const messages = payload.detail
      .map((entry) => (typeof entry.msg === "string" ? entry.msg.trim() : ""))
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return fallback;
}

function createPageTitle(pageNumber: number, phase: StoryPhase): string {
  switch (phase) {
    case "opening":
      return "Comienzo";
    case "ending":
      return "Desenlace";
    case "finished":
      return "Final";
    default:
      return `Escena ${pageNumber}`;
  }
}

function getNextScenePhase(currentPhase: StoryPhase): StoryPhase {
  if (currentPhase === "choice_2") {
    return "ending";
  }

  return "continuation";
}

function createBookPage(pageNumber: number, phase: StoryPhase, choiceUsed = ""): BookPage {
  return {
    id: pageNumber,
    phase,
    title: createPageTitle(pageNumber, phase),
    text: "",
    imageSrc: "",
    choiceUsed,
    selectedChoice: "",
    isGeneratingText: true,
    isGeneratingImage: false,
    isComplete: false,
    choices: [],
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
  const response = await fetch(`${resolveApiBaseUrl()}/stories/choices`, {
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
  const [appMode, setAppMode] = useState<AppMode>("setup");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [characterName, setCharacterName] = useState("");
  const [characterPersonality, setCharacterPersonality] = useState("");
  const [situationDescription, setSituationDescription] = useState("");
  const [drawingDescription, setDrawingDescription] = useState("");
  const [storyText, setStoryText] = useState("");
  const [storyState, setStoryState] = useState<StoryState>(EMPTY_STATE);
  const [pages, setPages] = useState<BookPage[]>([]);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [statusMessage, setStatusMessage] = useState("Sube un dibujo para comenzar la aventura.");
  const [isStarting, setIsStarting] = useState(false);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [isChoosing, setIsChoosing] = useState(false);

  const isBusy = isStarting || isGeneratingImage || isChoosing;
  const latestPageIndex = pages.length - 1;
  const viewedPage = currentPageIndex >= 0 ? pages[currentPageIndex] : undefined;
  const isViewingLatest = currentPageIndex === latestPageIndex;

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  function updatePage(pageId: number, updater: (page: BookPage) => BookPage) {
    setPages((current) =>
      current.map((page) => (page.id === pageId ? updater(page) : page)),
    );
  }

  function resetStoryState() {
    setAppMode("setup");
    setFile(null);
    setPreviewUrl("");
    setCharacterName("");
    setCharacterPersonality("");
    setSituationDescription("");
    setDrawingDescription("");
    setStoryText("");
    setStoryState(EMPTY_STATE);
    setPages([]);
    setCurrentPageIndex(0);
    setStatusMessage("Sube un dibujo para comenzar la aventura.");
    setIsStarting(false);
    setIsGeneratingImage(false);
    setIsChoosing(false);
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const nextFile = event.target.files?.[0] ?? null;
    setFile(nextFile);
    setPreviewUrl(nextFile ? URL.createObjectURL(nextFile) : "");
  }

  async function requestIllustration(
    pageId: number,
    nextStoryState: StoryState,
    nextDrawingDescription: string,
    storyContext: string,
    chosenAction: string,
  ): Promise<StoryState> {
    if (nextStoryState.image_count >= nextStoryState.max_images) {
      updatePage(pageId, (page) => ({
        ...page,
        isGeneratingImage: false,
      }));
      return nextStoryState;
    }

    setIsGeneratingImage(true);
    setStatusMessage("Generando la ilustracion de la escena...");
    updatePage(pageId, (page) => ({
      ...page,
      isGeneratingImage: true,
    }));

    try {
      const response = await fetch(`${resolveApiBaseUrl()}/images/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          character_name: characterName,
          character_personality: characterPersonality,
          drawing_description: nextDrawingDescription,
          situation_description: situationDescription,
          story_context: clampText(storyContext, IMAGE_STORY_CONTEXT_LIMIT),
          chosen_action: chosenAction,
        }),
      });

      if (!response.ok) {
        let errorMessage = "No se pudo crear la ilustracion.";
        try {
          const errorPayload = (await response.json()) as ErrorPayload;
          errorMessage = getErrorMessage(errorPayload, errorMessage);
        } catch {
          // Keep the fallback message when the API returns no JSON body.
        }
        throw new Error(errorMessage);
      }

      const payload = (await response.json()) as { image_base64: string; media_type: string };
      updatePage(pageId, (page) => ({
        ...page,
        imageSrc: `data:${payload.media_type};base64,${payload.image_base64}`,
        isGeneratingImage: false,
      }));
      return incrementImageCount(nextStoryState);
    } catch (error) {
      updatePage(pageId, (page) => ({
        ...page,
        isGeneratingImage: false,
      }));
      throw error;
    } finally {
      setIsGeneratingImage(false);
    }
  }

  async function handleStart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      return;
    }

    const firstPage = createBookPage(1, "opening");

    setIsStarting(true);
    setAppMode("reader");
    setPages([firstPage]);
    setCurrentPageIndex(0);
    setStoryText("");
    setStoryState(EMPTY_STATE);
    setDrawingDescription("");
    setStatusMessage("Analizando el dibujo...");

    try {
      const describeBody = new FormData();
      describeBody.append("image", file);
      describeBody.append("character_name", characterName);
      describeBody.append("character_personality", characterPersonality);

      const describeResponse = await fetch(`${resolveApiBaseUrl()}/characters/describe`, {
        method: "POST",
        body: describeBody,
      });

      if (!describeResponse.ok) {
        throw new Error("No se pudo analizar el dibujo.");
      }

      const describePayload = (await describeResponse.json()) as { drawing_description: string };
      setDrawingDescription(describePayload.drawing_description);
      setStatusMessage("Escribiendo el inicio de la historia...");

      const startResponse = await fetch(`${resolveApiBaseUrl()}/stories/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          character_name: characterName,
          character_personality: characterPersonality,
          drawing_description: describePayload.drawing_description,
          situation_description: situationDescription,
        }),
      });

      const doneEvent = await parseStoryStream(startResponse, (text) => {
        updatePage(firstPage.id, (page) => ({
          ...page,
          text,
        }));
      });

      setStoryText(doneEvent.story_text);
      updatePage(firstPage.id, (page) => ({
        ...page,
        text: doneEvent.current_scene_text,
        isGeneratingText: false,
      }));

      let nextStoryState = doneEvent.story_state;
      if (doneEvent.can_generate_image) {
        nextStoryState = await requestIllustration(
          firstPage.id,
          nextStoryState,
          describePayload.drawing_description,
          doneEvent.story_text,
          "",
        );
      }

      setStoryState(nextStoryState);
      setStatusMessage("Preparando opciones para continuar...");
      const nextChoices = await generateChoices(
        doneEvent.story_text,
        characterName,
        characterPersonality,
      );
      updatePage(firstPage.id, (page) => ({
        ...page,
        choices: nextChoices,
        isComplete: true,
      }));
      setStatusMessage("La historia ha comenzado.");
    } catch (error) {
      updatePage(firstPage.id, (page) => ({
        ...page,
        isGeneratingText: false,
        isGeneratingImage: false,
        isComplete: true,
      }));
      setStatusMessage(error instanceof Error ? error.message : "La historia no pudo comenzar.");
    } finally {
      setIsStarting(false);
    }
  }

  async function handleChoice(choice: string) {
    const scenePhase = getNextScenePhase(storyState.phase);
    const nextPage = createBookPage(pages.length + 1, scenePhase, choice);

    setIsChoosing(true);
    updatePage(pages[latestPageIndex].id, (page) => ({
      ...page,
      selectedChoice: choice,
      choices: [],
    }));
    setPages((current) => [...current, nextPage]);
    setCurrentPageIndex(pages.length);
    setStatusMessage("La aventura continua...");

    try {
      const response = await fetch(`${resolveApiBaseUrl()}/stories/continue`, {
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

      const doneEvent = await parseStoryStream(response, (text) => {
        updatePage(nextPage.id, (page) => ({
          ...page,
          text,
        }));
      });

      setStoryText(doneEvent.story_text);
      updatePage(nextPage.id, (page) => ({
        ...page,
        text: doneEvent.current_scene_text,
        isGeneratingText: false,
      }));

      let nextStoryState = doneEvent.story_state;
      if (doneEvent.can_generate_image) {
        nextStoryState = await requestIllustration(
          nextPage.id,
          nextStoryState,
          drawingDescription,
          doneEvent.story_text,
          choice,
        );
      }

      setStoryState(nextStoryState);

      if (doneEvent.is_finished) {
        updatePage(nextPage.id, (page) => ({
          ...page,
          phase: "finished",
          title: createPageTitle(nextPage.id, "finished"),
          isComplete: true,
        }));
        setStatusMessage("La historia ha terminado con un final tierno.");
        return;
      }

      setStatusMessage("Preparando nuevas opciones...");
      const nextChoices = await generateChoices(
        doneEvent.story_text,
        characterName,
        characterPersonality,
      );
      updatePage(nextPage.id, (page) => ({
        ...page,
        choices: nextChoices,
        isComplete: true,
      }));
      setStatusMessage("Elige como quieres continuar.");
    } catch (error) {
      updatePage(nextPage.id, (page) => ({
        ...page,
        isGeneratingText: false,
        isGeneratingImage: false,
        isComplete: true,
      }));
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
          Personaliza a tu protagonista y convierte cada escena en un libro ilustrado
          que se lee pagina a pagina.
        </p>
      </section>

      {appMode === "setup" ? (
        <section className="setup-layout">
          <aside className="panel panel--setup">
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
                {isStarting ? "Creando historia..." : "Generar historia"}
              </button>
            </form>
          </aside>

          <section className="panel setup-preview">
            <p className="status">{statusMessage}</p>
            {previewUrl ? (
              <div className="card">
                <h2>Preview del dibujo</h2>
                <img className="preview" src={previewUrl} alt="Preview del dibujo" />
              </div>
            ) : (
              <div className="card card--empty">
                <h2>Todo empieza aqui</h2>
                <p className="subtle">
                  Sube un dibujo y completa la personalizacion para pasar al modo lectura.
                </p>
              </div>
            )}
          </section>
        </section>
      ) : (
        <section className="reader-shell">
          <header className="reader-toolbar">
            <div className="reader-toolbar__copy">
              <p className="status">{statusMessage}</p>
              {viewedPage ? (
                <p className="subtle">
                  Pagina {currentPageIndex + 1} de {pages.length}
                  {isViewingLatest ? " · Escena actual" : " · Lectura de archivo"}
                </p>
              ) : null}
            </div>

            <div className="reader-toolbar__actions">
              <button
                className="secondary"
                type="button"
                onClick={() => setCurrentPageIndex((index) => Math.max(0, index - 1))}
                disabled={currentPageIndex === 0}
              >
                Anterior
              </button>
              <button
                className="secondary"
                type="button"
                onClick={() => setCurrentPageIndex((index) => Math.min(latestPageIndex, index + 1))}
                disabled={currentPageIndex >= latestPageIndex}
              >
                Siguiente
              </button>
              <button className="secondary" type="button" onClick={resetStoryState}>
                Nueva historia
              </button>
            </div>
          </header>

          <section className="book-spread">
            <article className="book-page">
              <div className="book-page__header">
                <p className="book-page__eyebrow">Pagina izquierda</p>
                <h2>{viewedPage?.title ?? "Ilustracion"}</h2>
                {viewedPage?.choiceUsed ? (
                  <p className="pill">Llegaste aqui por: {viewedPage.choiceUsed}</p>
                ) : null}
              </div>

              <div className="book-illustration">
                {viewedPage?.imageSrc ? (
                  <img className="story-image" src={viewedPage.imageSrc} alt={viewedPage.title} />
                ) : viewedPage?.isGeneratingImage || viewedPage?.isGeneratingText ? (
                  <div className="illustration-placeholder">
                    <div className="illustration-placeholder__glow" />
                    <p>Ilustrando la escena...</p>
                  </div>
                ) : (
                  <div className="illustration-placeholder illustration-placeholder--static">
                    <p>La ilustracion aparecera en esta pagina.</p>
                  </div>
                )}
              </div>
            </article>

            <article className="book-page">
              <div className="book-page__header">
                <p className="book-page__eyebrow">Pagina derecha</p>
                <h2>{viewedPage?.title ?? "Historia"}</h2>
              </div>

              <div className="book-copy">
                {viewedPage?.text ? (
                  <p className="story-copy">{viewedPage.text}</p>
                ) : (
                  <p className="subtle">El texto aparecera aqui a medida que se escriba la escena.</p>
                )}
              </div>

              {viewedPage?.selectedChoice && !isViewingLatest ? (
                <div className="history-note">
                  <p className="pill">Decision tomada: {viewedPage.selectedChoice}</p>
                </div>
              ) : null}

              {isViewingLatest && viewedPage ? (
                <div className="reader-options">
                  <h3>Como quieres continuar?</h3>
                  {viewedPage.isGeneratingText || viewedPage.isGeneratingImage ? (
                    <p className="subtle">
                      Las opciones apareceran cuando termine de escribirse e ilustrarse la escena.
                    </p>
                  ) : viewedPage.choices.length > 0 ? (
                    <div className="choices">
                      {viewedPage.choices.map((choice) => (
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
                  ) : storyState.phase === "finished" ? (
                    <p className="subtle">La historia ya termino y esta lista para releerse.</p>
                  ) : (
                    <p className="subtle">Las opciones estaran disponibles al completar la escena.</p>
                  )}
                </div>
              ) : viewedPage ? (
                <div className="history-note">
                  <p className="subtle">
                    Esta pagina es de solo lectura. Usa la navegacion para volver a la escena actual.
                  </p>
                </div>
              ) : null}
            </article>
          </section>
        </section>
      )}
    </main>
  );
}
