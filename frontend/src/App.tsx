import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import attachIcon from "../assets/icons/attach.png";
import cloudIcon from "../assets/icons/cloud.png";
import modelIcon from "../assets/icons/model.png";
import reviewBackground from "../assets/review_bg.png";

import { GenerationResponse, GenerationEvent } from "./types";
import { createGeneration, getGeneration, subscribeToEvents, cancelGeneration } from "./api";
import { LoadingScreen } from "./components/LoadingScreen";
import { ProjectWorkspace } from "./components/ProjectWorkspace";

const reviews = [
  {
    quote: "I described the page I had in mind and had a polished starting point in minutes. It feels like the gap between a sketch and something people can actually use has disappeared.",
    name: "Janet Jackson",
    role: "CEO @Unicorn Inc",
    initials: "JJ",
    tone: "violet",
  },
  {
    quote: "I was amazed by how quickly a simple idea became a functional layout. I shared the direction, watched it take shape, and could refine the details without losing momentum.",
    name: "Sofia Martinez",
    role: "Product manager @NovaLabs",
    initials: "SM",
    tone: "rose",
  },
  {
    quote: "Turning an early thought into a real design has never felt this easy. The result looks intentional, and iterating feels more like a conversation than a handoff.",
    name: "Daniel Kim",
    role: "UX designer @Brightwave",
    initials: "DK",
    tone: "blue",
  },
];

function Mark() {
  return <span className="brand-mark" aria-hidden="true" />;
}

function ArrowIcon() {
  return <span className="arrow-icon" aria-hidden="true">↑</span>;
}

const modelOptions = [
  { label: "Groq (GPT-OSS 20B)", value: "openai/gpt-oss-20b" },
  { label: "Groq (GPT-OSS 120B)", value: "openai/gpt-oss-120b" },
  { label: "Llama 3 70B", value: "llama3-70b-8192" },
  { label: "Llama 3 8B", value: "llama3-8b-8192" },
  { label: "Mixtral 8x7B", value: "mixtral-8x7b-32768" },
];

import { SnackbarToast } from "./components/SnackbarToast";

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState(modelOptions[0].value);
  const [attachment, setAttachment] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Active generation state
  const [activeGeneration, setActiveGeneration] = useState<GenerationResponse | null>(null);
  const [events, setEvents] = useState<GenerationEvent[]>([]);

  // Snackbar Toast Notice state
  const [toast, setToast] = useState<{ title: string; message: string; type?: "warning" | "error" | "info" } | null>(null);

  const fileInput = useRef<HTMLInputElement>(null);

  // SSE & Polling effect when activeGeneration is present
  useEffect(() => {
    if (!activeGeneration) return;
    const genId = activeGeneration.id;

    if (["completed", "failed", "cancelled"].includes(activeGeneration.state)) {
      return;
    }

    // 1. Subscribe to SSE events
    const unsubscribe = subscribeToEvents(
      genId,
      (evt) => {
        setEvents((prev) => {
          if (prev.some((e) => e.id === evt.id)) return prev;
          return [...prev, evt];
        });

        // Trigger snackbar notice if event contains token/rate limit warning
        const msg = evt.message.toLowerCase();
        if (msg.includes("token") || msg.includes("rate limit") || msg.includes("quota")) {
          setToast({
            title: "API & Token Notice",
            message: evt.message,
            type: "warning",
          });
        }
      },
      (err) => {
        console.warn("SSE connection interrupted, relying on status polling:", err);
      }
    );

    // 2. Poll status every 2 seconds
    const interval = setInterval(async () => {
      try {
        const latest = await getGeneration(genId);
        setActiveGeneration(latest);
        if (["completed", "failed", "cancelled"].includes(latest.state)) {
          clearInterval(interval);
          if (latest.state === "failed" && latest.error) {
            setToast({
              title: "Generation Pipeline Error",
              message: latest.error,
              type: "error",
            });
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, [activeGeneration?.id, activeGeneration?.state]);


  function clearUrlHash() {
    if (window.location.hash) {
      window.history.replaceState(null, "", window.location.pathname);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!prompt.trim() || isSubmitting) return;

    clearUrlHash();
    setIsSubmitting(true);
    setError(null);
    setEvents([]);

    try {
      const run = await createGeneration(prompt.trim(), model);
      setActiveGeneration(run);
    } catch (err: any) {
      setError(err.message || "Failed to submit project request.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCancel() {
    if (!activeGeneration) return;
    try {
      await cancelGeneration(activeGeneration.id);
      const latest = await getGeneration(activeGeneration.id);
      setActiveGeneration(latest);
    } catch (err) {
      console.error("Failed to cancel generation:", err);
    }
  }

  async function handleRetry() {
    const currentPrompt = activeGeneration?.prompt || prompt;
    if (!currentPrompt.trim() || isSubmitting) return;

    clearUrlHash();
    setIsSubmitting(true);
    setError(null);
    setEvents([]);

    try {
      const run = await createGeneration(currentPrompt.trim(), model);
      setActiveGeneration(run);
    } catch (err: any) {
      setError(err.message || "Failed to retry project generation.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleNewProject() {
    clearUrlHash();
    setActiveGeneration(null);
    setEvents([]);
    setError(null);
    setPrompt("");
  }

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) setAttachment(file.name);
  }

  function renderNavbar() {
    return (
      <nav className="nav shell" aria-label="Main navigation">
        <a className="brand" href="#home" onClick={handleNewProject}>
          <Mark /> <span className="brand-name">BuildBuddy</span>
        </a>
        <div className="nav-links">
          <a href="#how-it-works">How it works</a>
          <a href="#voices">Community</a>
          <a href="#footer">Documentation</a>
        </div>
        <a className="sign-in" href="#prompt">Sign in</a>
      </nav>
    );
  }

  return (
    <main>
      {/* Dynamic View Logic */}
      {activeGeneration ? (
        activeGeneration.state === "completed" ? (
          <ProjectWorkspace
            generation={activeGeneration}
            onNewProject={handleNewProject}
            userInitials="NK"
          />
        ) : (
          <LoadingScreen
            generation={activeGeneration}
            events={events}
            onCancel={handleCancel}
            onReturnHome={handleNewProject}
            onRetry={handleRetry}
          />
        )
      ) : (
        <>
          {/* Hero Section & Prompt Form */}
          <section className="hero" id="home">
            <div className="orb orb-one" />
            <div className="orb orb-two" />
            <div className="hero-grid" />
            {renderNavbar()}

            <div className="hero-content shell">
              <span className="eyebrow">✦ Your AI software engineer</span>
              <h1>
                Turn an idea into<br />
                <span>a working application</span>
              </h1>
              <p>
                Describe what you want to build. BuildBuddy plans, architects, and
                generates a thoughtful first version for you to explore.
              </p>

              <form className="prompt-card" id="prompt" onSubmit={submit}>
                <label className="sr-only" htmlFor="project-prompt">
                  Describe your project
                </label>
                <textarea
                  id="project-prompt"
                  value={prompt}
                  onChange={(event) => {
                    setPrompt(event.target.value);
                    setError(null);
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      if (prompt.trim() && !isSubmitting) {
                        event.currentTarget.form?.requestSubmit();
                      }
                    }
                  }}
                  placeholder="Build a modern calculator app in HTML, CSS, and JS..."
                  rows={3}
                  disabled={isSubmitting}
                />


                {error && <div className="error-banner">{error}</div>}

                <div className="prompt-actions">
                  <button
                    className="prompt-pill"
                    type="button"
                    aria-label="Project type: Web app"
                  >
                    <img className="pill-image" src={cloudIcon} alt="" />
                    Web App
                  </button>
                  <label className="model-picker">
                    <img className="pill-image" src={modelIcon} alt="" />
                    <span className="sr-only">Choose AI model</span>
                    <select
                      value={model}
                      onChange={(event) => setModel(event.target.value)}
                      disabled={isSubmitting}
                    >
                      {modelOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <input
                    ref={fileInput}
                    className="file-input"
                    type="file"
                    onChange={chooseFile}
                  />
                  <button
                    className={`prompt-pill attach-button ${
                      attachment ? "is-attached" : ""
                    }`}
                    type="button"
                    onClick={() => fileInput.current?.click()}
                  >
                    <img className="pill-image" src={attachIcon} alt="" />
                    {attachment ? `Attached: ${attachment}` : "Attach"}
                  </button>
                  <button
                    className="submit-button"
                    type="submit"
                    disabled={isSubmitting || !prompt.trim()}
                    aria-label="Generate project"
                  >
                    {isSubmitting ? "..." : <ArrowIcon />}
                  </button>
                </div>
              </form>
            </div>
            <a className="scroll-cue" href="#how-it-works">
              Scroll to explore <span>↓</span>
            </a>
          </section>

          {/* Workflow Section */}
          <section className="workflow shell" id="how-it-works">
            <p className="section-kicker">A clearer way to create</p>
            <h2>
              From prompt to project<br />
              in three deliberate steps
            </h2>
            <div className="steps">
              {[
                ["01", "Frame the idea", "Tell BuildBuddy what you want to build in your own words."],
                ["02", "See the blueprint", "Review the proposed stack, files, features, and implementation tasks."],
                ["03", "Start shipping", "Receive a structured project you can inspect, run, and make your own."],
              ].map(([number, title, copy]) => (
                <article className="step" key={number}>
                  <span>{number}</span>
                  <h3>{title}</h3>
                  <p>{copy}</p>
                </article>
              ))}
            </div>
          </section>

          {/* Reviews / Community Section */}
          <section className="voices" id="voices">
            <div
              className="review-background"
              style={{ backgroundImage: `url(${reviewBackground})` }}
              aria-hidden="true"
            />
            <div className="review-stack shell">
              {reviews.map((review, index) => (
                <article
                  className={`review review-${index + 1}`}
                  key={review.name}
                >
                  <div className={`avatar ${review.tone}`}>{review.initials}</div>
                  <div>
                    <p className="quote">“{review.quote}”</p>
                    <p className="person">
                      {review.name} <span>· {review.role}</span>
                    </p>
                  </div>
                  <div className="stars" aria-label="5 out of 5 stars">
                    ☆ ☆ ☆ ☆ ☆
                  </div>
                </article>
              ))}
            </div>
          </section>

          {/* Footer (Landing page only) */}
          <footer id="footer">
            <div className="shell footer-grid">
              <div className="footer-brand">
                <a className="brand" href="#home" onClick={handleNewProject}>
                  <Mark /> <span className="brand-name">BuildBuddy</span>
                </a>
                <p>
                  An AI-powered engineering companion that turns your words into
                  thoughtful, editable software.
                </p>
              </div>
              <div>
                <h3>Explore</h3>
                <a href="#home">Home</a>
                <a href="#how-it-works">How it works</a>
                <a href="#voices">Community</a>
                <a href="#prompt">Start building</a>
              </div>
              <div>
                <h3>Resources</h3>
                <a href="#footer">Documentation</a>
                <a href="#footer">Project guide</a>
                <a href="#footer">Changelog</a>
                <a href="#footer">Support</a>
              </div>
              <div>
                <h3>Legal</h3>
                <a href="#footer">Privacy</a>
                <a href="#footer">Terms</a>
                <a href="#footer">Cookies</a>
              </div>
            </div>
            <div className="shell copyright">
              © {new Date().getFullYear()} BuildBuddy. Built with curiosity.
            </div>
          </footer>
        </>
      )}

      {/* Bottom-Right Snackbar Toast Notification */}
      {toast && (
        <SnackbarToast
          title={toast.title}
          message={toast.message}
          type={toast.type}
          durationMs={6000}
          onClose={() => setToast(null)}
        />
      )}
    </main>
  );
}


