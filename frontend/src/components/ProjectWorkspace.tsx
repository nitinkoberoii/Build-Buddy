import React, { useEffect, useState } from "react";
import { GenerationResponse, FileNode } from "../types";
import { getFileTree, getFileContent, getDownloadUrl } from "../api";
import { FileTree } from "./FileTree";
import { CodeViewer } from "./CodeViewer";

interface ProjectWorkspaceProps {
  generation: GenerationResponse;
  onNewProject: () => void;
}

export const ProjectWorkspace: React.FC<ProjectWorkspaceProps> = ({
  generation,
  onNewProject,
}) => {
  const [files, setFiles] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [isLoadingFiles, setIsLoadingFiles] = useState<boolean>(true);
  const [isLoadingContent, setIsLoadingContent] = useState<boolean>(false);

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

  const downloadUrl = getDownloadUrl(generation.id);
  const plan = generation.plan;

  return (
    <div className="workspace-container shell">
      <div className="workspace-header">
        <div className="workspace-title-group">
          <span className="workspace-badge mono-text">READY TO RUN</span>
          <h2 className="workspace-title">{plan?.name || "Generated Application"}</h2>
          <p className="workspace-desc">{plan?.description || generation.prompt}</p>
          {plan?.techstack && (
            <div className="tech-stack-pills">
              {plan.techstack.split(",").map((tech) => (
                <span key={tech.trim()} className="tech-pill mono-text">
                  {tech.trim()}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="workspace-actions">
          <a
            href={downloadUrl}
            className="download-btn"
            download={`buildbuddy-${generation.id.slice(0, 8)}.zip`}
          >
            <span>↓</span> Download .ZIP Archive
          </a>
          <button className="new-proj-btn" onClick={onNewProject} type="button">
            ＋ Start New Project
          </button>
        </div>
      </div>

      <div className="workspace-split">
        <aside className="workspace-sidebar">
          {plan?.features && plan.features.length > 0 && (
            <div className="sidebar-section">
              <h3 className="section-title">Included Features</h3>
              <ul className="features-list">
                {plan.features.map((feat, i) => (
                  <li key={i} className="feature-item">
                    <span className="check-icon">✓</span> {feat}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="sidebar-section file-explorer-section">
            <h3 className="section-title">Project Files</h3>
            {isLoadingFiles ? (
              <div className="tree-loading mono-text">Loading file tree...</div>
            ) : (
              <FileTree
                nodes={files}
                selectedPath={selectedFile}
                onSelectFile={(path) => setSelectedFile(path)}
              />
            )}
          </div>
        </aside>

        <main className="workspace-main">
          {selectedFile ? (
            <CodeViewer
              path={selectedFile}
              content={fileContent}
              isLoading={isLoadingContent}
            />
          ) : (
            <div className="empty-code-panel text-muted">
              Select a file from the explorer on the left to inspect code.
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
