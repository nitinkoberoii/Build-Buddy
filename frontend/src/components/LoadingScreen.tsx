import React, { useEffect, useRef, useState } from "react";
import { GenerationResponse, GenerationEvent, GenerationState } from "../types";

interface LoadingScreenProps {
  generation: GenerationResponse;
  events: GenerationEvent[];
  onCancel: () => void;
  onReturnHome?: () => void;
  onRetry?: () => void;
}

function getStageLabel(state: GenerationState): { stage: string; title: string; desc: string } {
  switch (state) {
    case "queued":
      return {
        stage: "QUEUED",
        title: "Initializing workspace environment",
        desc: "Allocating isolated run container and environment configuration...",
      };
    case "planning":
      return {
        stage: "PLANNER",
        title: "Analyzing prompt & architectural requirements",
        desc: "Selecting tech stack, defining features, and mapping file structures...",
      };
    case "architecting":
      return {
        stage: "ARCHITECT",
        title: "Creating file-level task blueprint",
        desc: "Breaking down implementation steps into structured engineering tasks...",
      };
    case "coding":
      return {
        stage: "CODER",
        title: "Writing and generating project files",
        desc: "Executing implementation tasks and generating HTML, CSS, and JS code...",
      };
    case "completed":
      return {
        stage: "COMPLETED",
        title: "Starter project ready",
        desc: "Finalizing generated files and preparing project workspace...",
      };
    case "failed":
      return {
        stage: "FAILED",
        title: "Generation Pipeline Error",
        desc: "An issue occurred during agent execution.",
      };
    case "cancelled":
      return {
        stage: "CANCELLED",
        title: "Generation run was cancelled",
        desc: "Background execution has been terminated.",
      };
    default:
      return {
        stage: "PROCESSING",
        title: "Building your application",
        desc: "Processing engineering pipeline steps...",
      };
  }
}

function getHumanReadableError(errorMsg?: string, lastEventMsg?: string): { summary: string; detail: string; suggestion: string } {
  const combined = `${errorMsg || ""} ${lastEventMsg || ""}`.toLowerCase();

  if (
    combined.includes("validationerror") ||
    combined.includes("input should be a valid dictionary") ||
    combined.includes("model_type")
  ) {
    return {
      summary: "AI Output Formatting Issue",
      detail:
        "The AI model returned a step response format that did not match the required schema during architectural planning.",
      suggestion:
        "We've applied sanitization on the backend. Click 'Try Again' to re-run the generation or choose a larger model.",
    };
  }

  if (combined.includes("rate_limit") || combined.includes("429") || combined.includes("quota")) {
    return {
      summary: "Provider Rate Limit Reached",
      detail: "The AI provider (Groq) rate limit was temporarily exceeded.",
      suggestion: "Wait 10-15 seconds and click 'Try Again'.",
    };
  }

  if (combined.includes("timeout") || combined.includes("timed out")) {
    return {
      summary: "Execution Timeout",
      detail: "The code generation task took longer than the maximum allowed timeout limit.",
      suggestion: "Click 'Try Again' to retry generation.",
    };
  }

  if (combined.includes("groq_api_key") || combined.includes("api_key") || combined.includes("unauthorized")) {
    return {
      summary: "API Authentication Error",
      detail: "Missing or invalid Groq API key configuration on the server.",
      suggestion: "Please check that GROQ_API_KEY is configured in your server environment.",
    };
  }

  return {
    summary: "Assembly Execution Error",
    detail: errorMsg || lastEventMsg || "An unexpected error occurred while generating codebase files.",
    suggestion: "Click 'Try Again' to retry the generation process or return home to adjust your prompt.",
  };
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
  generation,
  events,
  onCancel,
  onReturnHome,
  onRetry,
}) => {
  const [showLogs, setShowLogs] = useState(false);
  const [countdown, setCountdown] = useState<number | null>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const { stage, title, desc } = getStageLabel(generation.state);

  const isCancelled = generation.state === "cancelled";
  const isFailed = generation.state === "failed";

  // 5-second auto-return countdown timer on cancellation
  useEffect(() => {
    if (isCancelled) {
      setCountdown(5);
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev === null || prev <= 1) {
            clearInterval(timer);
            if (onReturnHome) onReturnHome();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [isCancelled, onReturnHome]);

  // Auto-scroll terminal drawer
  useEffect(() => {
    if (showLogs && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [events, showLogs]);

  const latestEvent = events.length > 0 ? events[events.length - 1] : null;
  const humanError = getHumanReadableError(generation.error, latestEvent?.message);
  const ticketId = `BB-FAIL-${generation.id.slice(0, 8).toUpperCase()}`;

  return (
    <div className="loading-screen-container shell">
      <div className="loading-content">
        {isFailed ? (
          /* Failed Generation Incident Ticket Card */
          <div className="failed-ticket-card">
            <div className="ticket-header-bar">
              <div className="ticket-id-badge mono-text">
                TICKET #{ticketId}
              </div>
              <div className="ticket-status-pill mono-text">
                ● GENERATION FAILED
              </div>
            </div>

            <div className="ticket-body">
              <div className="ticket-title-group">
                <span className="ticket-warning-icon">⚠️</span>
                <div>
                  <h3 className="ticket-title">{humanError.summary}</h3>
                  <p className="ticket-subtitle">{humanError.detail}</p>
                </div>
              </div>

              <div className="ticket-info-box">
                <div className="info-row">
                  <span className="info-label">💡 Recommended Action:</span>
                  <span className="info-val">{humanError.suggestion}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">🎯 Request Prompt:</span>
                  <span className="info-val prompt-val">“{generation.prompt}”</span>
                </div>
                <div className="info-row">
                  <span className="info-label">⚙️ Pipeline Stage:</span>
                  <span className="info-val mono-text stage-val">
                    [{generation.state.toUpperCase()}]
                  </span>
                </div>
              </div>

              {generation.error && (
                <details className="ticket-raw-details">
                  <summary className="mono-text">
                    Inspect Raw Diagnostics Log
                  </summary>
                  <pre className="raw-error-pre mono-text">{generation.error}</pre>
                </details>
              )}
            </div>

            {/* Ticket CTA Actions */}
            <div className="ticket-actions">
              {onRetry && (
                <button className="ticket-btn retry-btn" type="button" onClick={onRetry}>
                  🔄 Try Again
                </button>
              )}

              {onReturnHome && (
                <button className="ticket-btn home-btn" type="button" onClick={onReturnHome}>
                  🏠 Return to Home
                </button>
              )}

              <button
                className="ticket-btn logs-btn mono-text"
                type="button"
                onClick={() => setShowLogs(!showLogs)}
              >
                {showLogs ? "Hide Terminal Logs ▲" : "📜 Diagnostic Logs ▼"}
              </button>
            </div>
          </div>
        ) : (
          /* Normal Progress / Wavelength View */
          <>
            {/* Animated Concentric Wavelength Logo Wrapper */}
            <div className="wavelength-wrapper">
              <div className="wavelength-ring wavelength-ring-1" />
              <div className="wavelength-ring wavelength-ring-2" />
              <div className="wavelength-ring wavelength-ring-3" />
              <div className="wavelength-ring wavelength-ring-4" />

              <div className="logo-core" aria-label="BuildBuddy Logo">
                <div className="logo-inner-ring" />
              </div>
            </div>

            {/* Stage Status Info */}
            <div className="loading-status-group">
              <div className={`stage-pill mono-text ${isCancelled ? "is-cancelled-pill" : ""}`}>
                <span className="pulse-dot" />
                <span>{stage} {isCancelled ? "" : "AGENT"}</span>
              </div>

              <h2 className="loading-title">{title}</h2>
              <p className="loading-desc">{desc}</p>

              {isCancelled ? (
                <div className="latest-log-banner is-cancelled-banner mono-text">
                  <span className="log-arrow-warning">⚠</span> Generation run was cancelled by user
                </div>
              ) : (
                latestEvent && (
                  <div className="latest-log-banner mono-text">
                    <span className="log-arrow">▶</span> {latestEvent.message}
                  </div>
                )
              )}

              {isCancelled && countdown !== null && (
                <div className="return-timer mono-text">
                  <span>↪</span> Returning to home screen in {countdown} seconds...
                </div>
              )}

              <p className="prompt-preview">“{generation.prompt}”</p>
            </div>

            {/* Controls: Cancel & Toggle Terminal Logs */}
            <div className="loading-actions">
              <button
                className="toggle-logs-btn mono-text"
                type="button"
                onClick={() => setShowLogs(!showLogs)}
              >
                {showLogs ? "Hide Terminal Logs ▲" : "Show Terminal Logs ▼"}
              </button>
              {!isCancelled && (
                <button className="cancel-run-btn" type="button" onClick={onCancel}>
                  Cancel Generation
                </button>
              )}
            </div>
          </>
        )}

        {/* Collapsible Terminal Log Drawer */}
        {showLogs && (
          <div className="terminal-drawer">
            <div className="drawer-bar mono-text">
              <span>live-agent-events.log</span>
              <span>{events.length} events</span>
            </div>
            <div className="drawer-body" ref={logRef}>
              {events.length === 0 ? (
                <div className="drawer-empty text-muted">Waiting for events...</div>
              ) : (
                events.map((evt) => (
                  <div key={evt.id} className="drawer-line">
                    <span className="drawer-time mono-text">
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </span>
                    <span className={`drawer-tag mono-text tag-${evt.stage}`}>
                      [{evt.stage.toUpperCase()}]
                    </span>
                    <span className="drawer-msg">{evt.message}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
