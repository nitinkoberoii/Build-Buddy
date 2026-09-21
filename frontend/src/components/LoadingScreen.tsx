import React, { useEffect, useRef, useState } from "react";
import { GenerationResponse, GenerationEvent, GenerationState } from "../types";

interface LoadingScreenProps {
  generation: GenerationResponse;
  events: GenerationEvent[];
  onCancel: () => void;
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
    default:
      return {
        stage: "PROCESSING",
        title: "Building your application",
        desc: "Processing engineering pipeline steps...",
      };
  }
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
  generation,
  events,
  onCancel,
}) => {
  const [showLogs, setShowLogs] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);
  const { stage, title, desc } = getStageLabel(generation.state);

  // Auto-scroll logs when open
  useEffect(() => {
    if (showLogs && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [events, showLogs]);

  const latestEvent = events.length > 0 ? events[events.length - 1] : null;

  return (
    <div className="loading-screen-container shell">
      <div className="loading-content">
        {/* Animated Concentric Wavelength Logo Wrapper */}
        <div className="wavelength-wrapper">
          {/* Animated concentric wavelength rings */}
          <div className="wavelength-ring wavelength-ring-1" />
          <div className="wavelength-ring wavelength-ring-2" />
          <div className="wavelength-ring wavelength-ring-3" />
          <div className="wavelength-ring wavelength-ring-4" />

          {/* Central BuildBuddy Circular Ring Logo */}
          <div className="logo-core" aria-label="BuildBuddy Logo">
            <div className="logo-inner-ring" />
          </div>
        </div>

        {/* Stage Status Info */}
        <div className="loading-status-group">
          <div className="stage-pill mono-text">
            <span className="pulse-dot" />
            <span>{stage} AGENT</span>
          </div>

          <h2 className="loading-title">{title}</h2>
          <p className="loading-desc">{desc}</p>

          {latestEvent && (
            <div className="latest-log-banner mono-text">
              <span className="log-arrow">▶</span> {latestEvent.message}
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
          <button className="cancel-run-btn" type="button" onClick={onCancel}>
            Cancel Generation
          </button>
        </div>

        {/* Optional Collapsible Terminal Log Drawer */}
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
