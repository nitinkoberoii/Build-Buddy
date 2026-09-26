import React, { useEffect, useState, useRef, useCallback } from "react";
import { GenerationResponse, FileNode, ThreadMessage } from "../types";
import { getFileTree, getFileContent, getDownloadUrl, refineGeneration, getGeneration, subscribeToEvents } from "../api";
import { FileTree } from "./FileTree";
import { CodeViewer } from "./CodeViewer";

interface ProjectWorkspaceProps {
  generation: GenerationResponse;
  onNewProject: () => void;
  userInitials?: string;
}

export const ProjectWorkspace: React.FC<ProjectWorkspaceProps> = ({
  generation: initialGeneration,
  onNewProject,
  userInitials = "NK",
}) => {
  const [generation, setGeneration] = useState<GenerationResponse>(initialGeneration);
  const [files, setFiles] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [isLoadingFiles, setIsLoadingFiles] = useState<boolean>(true);
  const [isLoadingContent, setIsLoadingContent] = useState<boolean>(false);

  // Refinement thread state
  const [refinementPrompt, setRefinementPrompt] = useState<string>("");
  const [isRefining, setIsRefining] = useState<boolean>(false);
  const [refinementError, setRefinementError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Resizable split percentage state (default 35% left, 65% right)
  const [leftWidthPercent, setLeftWidthPercent] = useState<number>(35);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const splitContainerRef = useRef<HTMLDivElement>(null);

  // Update generation state when prop changes
  useEffect(() => {
    setGeneration(initialGeneration);
  }, [initialGeneration]);

  // Helper to load file tree
  const refreshFileTree = useCallback(
    async (keepSelected: boolean = true) => {
      setIsLoadingFiles(true);
      try {
        const nodes = await getFileTree(generation.id);
        setFiles(nodes);

        if (!selectedFile || !keepSelected) {
          const firstFile = findFirstFile(nodes);
          if (firstFile) {
            setSelectedFile(firstFile.path);
          }
        }
      } catch (err) {
        console.error("Error loading file tree:", err);
      } finally {
        setIsLoadingFiles(false);
      }
    },
    [generation.id, selectedFile]
  );

  // Helper to load file content
  const refreshFileContent = useCallback(
    async (path: string) => {
      setIsLoadingContent(true);
      try {
        const res = await getFileContent(generation.id, path);
        setFileContent(res.content);
      } catch (err) {
        console.error("Error reading file:", err);
      } finally {
        setIsLoadingContent(false);
      }
    },
    [generation.id]
  );

  // File tree initial loading
  useEffect(() => {
    refreshFileTree(false);
  }, [generation.id]);

  // File content loading
  useEffect(() => {
    if (selectedFile) {
      refreshFileContent(selectedFile);
    }
  }, [selectedFile]);

  // Scroll to bottom of thread messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [generation.messages, isRefining]);

  // Handle refinement submission
  async function handleRefinementSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!refinementPrompt.trim() || isRefining) return;

    const promptText = refinementPrompt.trim();
    setRefinementPrompt("");
    setIsRefining(true);
    setRefinementError(null);

    // Optimistically update local message thread
    const userMsg: ThreadMessage = {
      id: "temp-user-" + Date.now(),
      role: "user",
      content: promptText,
      timestamp: new Date().toISOString(),
    };

    const asstMsg: ThreadMessage = {
      id: "temp-asst-" + Date.now(),
      role: "assistant",
      content: "Analyzing codebase and applying requested edits...",
      timestamp: new Date().toISOString(),
      status: "refining",
    };

    setGeneration((prev) => ({
      ...prev,
      messages: [...(prev.messages || []), userMsg, asstMsg],
    }));

    try {
      const updatedGen = await refineGeneration(generation.id, promptText);
      setGeneration(updatedGen);

      // Poll status until completion
      const pollInterval = setInterval(async () => {
        try {
          const latest = await getGeneration(generation.id);
          setGeneration(latest);

          const lastMsg = latest.messages?.[latest.messages.length - 1];
          if (!lastMsg || lastMsg.status !== "refining") {
            clearInterval(pollInterval);
            setIsRefining(false);
            // Refresh file tree and active file content
            await refreshFileTree(true);
            if (selectedFile) {
              await refreshFileContent(selectedFile);
            }
          }
        } catch (err) {
          console.error("Error polling refinement status:", err);
          clearInterval(pollInterval);
          setIsRefining(false);
        }
      }, 1500);

    } catch (err: any) {
      console.error("Refinement submission error:", err);
      setRefinementError(err.message || "Failed to submit edit prompt");
      setIsRefining(false);
    }
  }

  function findFirstFile(nodes: FileNode[]): FileNode | null {
    for (const node of nodes) {
      if (node.type === "file") {
        if (node.name.toLowerCase() === "index.html") return node;
      }
      if (node.children) {
        const found = findFirstFile(node.children);
        if (found) return found;
      }
    }
    for (const node of nodes) {
      if (node.type === "file") return node;
    }
    return null;
  }

  // Count total files
  function countFiles(nodes: FileNode[]): number {
    let total = 0;
    for (const node of nodes) {
      if (node.type === "file") total++;
      if (node.children) total += countFiles(node.children);
    }
    return total;
  }

  // Drag-to-resize split pane handler
  const handleMouseDown = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent | TouchEvent) => {
      if (!isDragging || !splitContainerRef.current) return;

      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      const rect = splitContainerRef.current.getBoundingClientRect();
      const offset = clientX - rect.left;
      const totalWidth = rect.width;

      if (totalWidth <= 0) return;

      let newPercent = (offset / totalWidth) * 100;
      // Clamp between 20% and 75%
      if (newPercent < 20) newPercent = 20;
      if (newPercent > 75) newPercent = 75;

      setLeftWidthPercent(newPercent);
    },
    [isDragging]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
      window.addEventListener("touchmove", handleMouseMove);
      window.addEventListener("touchend", handleMouseUp);
    } else {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      window.removeEventListener("touchmove", handleMouseMove);
      window.removeEventListener("touchend", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      window.removeEventListener("touchmove", handleMouseMove);
      window.removeEventListener("touchend", handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const downloadUrl = getDownloadUrl(generation.id);
  const plan = generation.plan;
  const projectName = plan?.name || "Generated Application";
  const totalFileCount = countFiles(files);
  const messages = generation.messages || [];

  return (
    <div className={`workspace-view-root ${isDragging ? "is-resizing" : ""}`}>
      {/* Top Header matching wireframe specs */}
      <header className="workspace-top-header">
        <div className="header-brand-group">
          <a className="brand" href="#home" onClick={onNewProject}>
            <span className="brand-mark" aria-hidden="true" />
            <span className="brand-name">BuildBuddy</span>
          </a>
          <span className="header-divider" />
          <div className="header-project-pill mono-text" title={projectName}>
            <span className="pill-dot green-dot" />
            <span className="project-title-text">{projectName}</span>
          </div>
        </div>

        <div className="header-right-group">
          <a
            href={downloadUrl}
            className="header-action-btn download-zip-btn"
            download={`buildbuddy-${generation.id.slice(0, 8)}.zip`}
          >
            <span>↓</span> Download .ZIP
          </a>

          <button
            className="header-action-btn new-project-btn"
            onClick={onNewProject}
            type="button"
          >
            ＋ Start New Project
          </button>

          {/* Rightmost User Profile Avatar */}
          <div className="user-profile-avatar" title="User Profile">
            {userInitials}
          </div>
        </div>
      </header>

      {/* Main Workspace Split Layout: 35% Left Container, 65% Right Container */}
      <div className="workspace-split-container" ref={splitContainerRef}>
        {/* Container 1: Left Container (35% default, Code files / Repo Tree + AI Refinement Prompt Box) */}
        <div
          className="workspace-container-card left-container"
          style={{ flexBasis: `${leftWidthPercent}%`, width: `${leftWidthPercent}%` }}
        >
          <div className="container-header-bar">
            <div className="container-header-badges">
              <div className="header-badge project-name-badge" title={projectName}>
                <span className="badge-icon">📦</span>
                <span className="badge-text mono-text">{projectName}</span>
              </div>
            </div>
            <div className="container-header-info mono-text">
              {totalFileCount > 0 ? `${totalFileCount} files` : "Repository"}
            </div>
          </div>

          <div className="left-container-body custom-scrollbar">
            {isLoadingFiles ? (
              <div className="tree-loading mono-text">Loading repository tree...</div>
            ) : (
              <FileTree
                nodes={files}
                selectedPath={selectedFile}
                onSelectFile={(path) => setSelectedFile(path)}
              />
            )}
          </div>

          {/* AI Refinement & Edit Prompt Panel below File Tree */}
          <div className="thread-refinement-panel">
            <div className="thread-panel-header">
              <span className="panel-title">✦ Edit Files with AI</span>
              {isRefining && <span className="refinement-status-badge">Updating files...</span>}
            </div>

            {/* Thread Message History */}
            {messages.length > 0 && (
              <div className="thread-messages-list custom-scrollbar">
                {messages.map((msg) => (
                  <div key={msg.id} className={`thread-message-item role-${msg.role}`}>
                    <div className="msg-header">
                      <span className="msg-role-label">
                        {msg.role === "user" ? "You" : "BuildBuddy AI"}
                      </span>
                      <span className="msg-time">
                        {new Date(msg.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                    <div className="msg-body">{msg.content}</div>
                    {msg.files_changed && msg.files_changed.length > 0 && (
                      <div className="msg-changed-files">
                        <span className="changed-label">Updated: </span>
                        {msg.files_changed.map((f) => (
                          <span
                            key={f}
                            className="changed-file-pill"
                            onClick={() => setSelectedFile(f)}
                            title={`Click to view ${f}`}
                          >
                            {f}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}

            {refinementError && (
              <div className="refinement-error-banner">{refinementError}</div>
            )}

            {/* Refinement Prompt Form */}
            <form className="thread-prompt-form" onSubmit={handleRefinementSubmit}>
              <textarea
                className="thread-prompt-input"
                value={refinementPrompt}
                onChange={(e) => setRefinementPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (refinementPrompt.trim() && !isRefining) {
                      handleRefinementSubmit(e as any);
                    }
                  }
                }}
                placeholder="Prompt to change files or add a feature..."
                rows={2}
                disabled={isRefining}
              />
              <button
                className="thread-send-btn"
                type="submit"
                disabled={isRefining || !refinementPrompt.trim()}
                title="Submit edit prompt"
              >
                {isRefining ? "..." : "↑"}
              </button>
            </form>
          </div>
        </div>

        {/* Resizer / Splitter Gutter */}
        <div
          className={`resizer-gutter ${isDragging ? "is-active" : ""}`}
          onMouseDown={handleMouseDown}
          onTouchStart={handleMouseDown}
          title="Drag to resize panels"
        >
          <div className="gutter-handle" />
        </div>

        {/* Container 2: Right Container (65% default, File Preview & Code Editor) */}
        <div
          className="workspace-container-card right-container"
          style={{
            flexBasis: `${100 - leftWidthPercent}%`,
            width: `${100 - leftWidthPercent}%`,
          }}
        >
          {selectedFile ? (
            <CodeViewer
              path={selectedFile}
              content={fileContent}
              isLoading={isLoadingContent}
              onContentChange={(newVal) => setFileContent(newVal)}
            />
          ) : (
            <div className="empty-code-panel text-muted">
              Select a file from the explorer on the left to inspect and edit code.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

