import { ChangeEvent, FormEvent, useRef, useState } from "react";
import attachIcon from "../assets/icons/attach.png";
import cloudIcon from "../assets/icons/cloud.png";
import modelIcon from "../assets/icons/model.png";
import reviewBackground from "../assets/review_bg.png";

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

const modelOptions = ["Groq", "GPT-5", "Claude Opus", "Gemini 2.5 Pro", "Llama 4 Maverick"];

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [sent, setSent] = useState(false);
  const [model, setModel] = useState("Groq");
  const [attachment, setAttachment] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!prompt.trim()) return;
    setSent(true);
  }

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) setAttachment(file.name);
  }

  return (
    <main>
      <section className="hero" id="home">
        <div className="orb orb-one" />
        <div className="orb orb-two" />
        <div className="hero-grid" />
        <nav className="nav shell" aria-label="Main navigation">
          <a className="brand" href="#home"><Mark /> <span className="brand-name">BuildBuddy</span></a>
          <div className="nav-links">
            <a href="#how-it-works">How it works</a>
            <a href="#voices">Community</a>
            <a href="#footer">Documentation</a>
          </div>
          <a className="sign-in" href="#prompt">Sign in</a>
        </nav>

        <div className="hero-content shell">
          <span className="eyebrow">✦ Your AI software engineer</span>
          <h1>Turn an idea into<br /><span>a working application</span></h1>
          <p>Describe what you want to build. BuildBuddy plans, architects, and generates a thoughtful first version for you to explore.</p>

          <form className="prompt-card" id="prompt" onSubmit={submit}>
            <label className="sr-only" htmlFor="project-prompt">Describe your project</label>
            <textarea
              id="project-prompt"
              value={prompt}
              onChange={(event) => { setPrompt(event.target.value); setSent(false); }}
              placeholder="Start creating something beautiful..."
              rows={3}
            />
            <div className="prompt-actions">
              <button
                className="prompt-pill"
                type="button"
                aria-label="Project type: Landing page"
              >
                <img className="pill-image" src={cloudIcon} alt="" />
                Landing page
              </button>
              <label className="model-picker">
                <img className="pill-image" src={modelIcon} alt="" />
                <span className="sr-only">Choose AI model</span>
                <select value={model} onChange={(event) => setModel(event.target.value)}>
                  {modelOptions.map((option) => <option key={option} value={option}>{option}</option>)}
                </select>
              </label>
              <input ref={fileInput} className="file-input" type="file" onChange={chooseFile} />
              <button className={`prompt-pill attach-button ${attachment ? "is-attached" : ""}`} type="button" onClick={() => fileInput.current?.click()}>
                <img className="pill-image" src={attachIcon} alt="" />
                {attachment ? `Attached: ${attachment}` : "Attach"}
              </button>
              <button className="submit-button" type="submit" aria-label="Generate project"><ArrowIcon /></button>
            </div>
            {sent && <p className="form-note">Ready to generate — API integration is the next backend milestone.</p>}
          </form>
        </div>
        <a className="scroll-cue" href="#how-it-works">Scroll to explore <span>↓</span></a>
      </section>

      <section className="workflow shell" id="how-it-works">
        <p className="section-kicker">A clearer way to create</p>
        <h2>From prompt to project<br />in three deliberate steps</h2>
        <div className="steps">
          {[
            ["01", "Frame the idea", "Tell BuildBuddy what you want to build in your own words."],
            ["02", "See the blueprint", "Review the proposed stack, files, features, and implementation tasks."],
            ["03", "Start shipping", "Receive a structured project you can inspect, run, and make your own."],
          ].map(([number, title, copy]) => (
            <article className="step" key={number}>
              <span>{number}</span><h3>{title}</h3><p>{copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="voices" id="voices">
        <div className="review-background" style={{ backgroundImage: `url(${reviewBackground})` }} aria-hidden="true" />
        <div className="review-stack shell">
          {reviews.map((review, index) => (
            <article className={`review review-${index + 1}`} key={review.name}>
              <div className={`avatar ${review.tone}`}>{review.initials}</div>
              <div>
                <p className="quote">“{review.quote}”</p>
                <p className="person">{review.name} <span>· {review.role}</span></p>
              </div>
              <div className="stars" aria-label="5 out of 5 stars">☆ ☆ ☆ ☆ ☆</div>
            </article>
          ))}
        </div>
      </section>

      <footer id="footer">
        <div className="shell footer-grid">
          <div className="footer-brand"><a className="brand" href="#home"><Mark /> <span className="brand-name">BuildBuddy</span></a><p>An AI-powered engineering companion that turns your words into thoughtful, editable software.</p></div>
          <div><h3>Explore</h3><a href="#home">Home</a><a href="#how-it-works">How it works</a><a href="#voices">Community</a><a href="#prompt">Start building</a></div>
          <div><h3>Resources</h3><a href="#footer">Documentation</a><a href="#footer">Project guide</a><a href="#footer">Changelog</a><a href="#footer">Support</a></div>
          <div><h3>Legal</h3><a href="#footer">Privacy</a><a href="#footer">Terms</a><a href="#footer">Cookies</a></div>
        </div>
        <div className="shell copyright">© {new Date().getFullYear()} BuildBuddy. Built with curiosity.</div>
      </footer>
    </main>
  );
}
