import React, { useEffect, useState, useRef, useCallback } from "react";
import { GenerationResponse, FileNode } from "../types";
import { getFileTree, getFileContent, getDownloadUrl } from "../api";
import { FileTree } from "./FileTree";
import { CodeViewer } from "./CodeViewer";

interface ProjectWorkspaceProps {
  generation: GenerationResponse;
  onNewProject: () => void;
  userInitials?: string;
}

export const ProjectWorkspace: React.FC<ProjectWorkspaceProps> = ({
  generation,
  onNewProject,
  userInitials = "NK",
}) => {
  const [files, setFiles] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [isLoadingFiles, setIsLoadingFiles] = useState<boolean>(true);
  const [isLoadingContent, setIsLoadingContent] = useState<boolean>(false);

  // Resizable split percentage state (default 35% left, 65% right)
  const [leftWidthPercent, setLeftWidthPercent] = useState<number>(35);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const splitContainerRef = useRef<HTMLDivElement>(null);

  // File tree fetching
  useEffect(() => {
    let isMounted = true;
    setIsLoadingFiles(true);

    getFileTree(generation.id)
      .then((nodes) => {
        if (!isMounted) return;
        setFiles(nodes);

        const firstFile = findFirstFile(nodes);
        if (firstFile) {
          setSelectedFile(firstFile.path);
        }
      })
      .catch((err) => console.error("Error loading file tree:", err))
      .finally(() => {
        if (isMounted) setIsLoadingFiles(false);
      });

    return () => {
      isMounted = false;
    };
  }, [generation.id]);

  // File content fetching
  useEffect(() => {
    if (!selectedFile) return;
    let isMounted = true;
    setIsLoadingContent(true);

    getFileContent(generation.id, selectedFile)
      .then((res) => {
        if (!isMounted) return;
        setFileContent(res.content);
      })
      .catch((err) => console.error("Error reading file:", err))
      .finally(() => {
        if (isMounted) setIsLoadingContent(false);
      });

    return () => {
      isMounted = false;
    };
  }, [generation.id, selectedFile]);

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
        {/* Container 1: Left Container (35% default, Code files / Repo Tree) */}
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
