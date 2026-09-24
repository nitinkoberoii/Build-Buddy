import React, { useState, useEffect, useRef } from "react";

interface CodeViewerProps {
  path: string;
  content: string;
  isLoading?: boolean;
  onContentChange?: (newContent: string) => void;
}

export function getLanguageFromPath(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "html":
    case "htm":
      return "HTML";
    case "css":
      return "CSS";
    case "js":
    case "jsx":
      return "JavaScript";
    case "ts":
    case "tsx":
      return "TypeScript";
    case "json":
      return "JSON";
    case "md":
      return "Markdown";
    case "py":
      return "Python";
    case "svg":
      return "SVG";
    case "txt":
      return "Text";
    default:
      return ext ? ext.toUpperCase() : "Plain Text";
  }
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  path,
  content,
  isLoading,
  onContentChange,
}) => {
  const [localContent, setLocalContent] = useState(content);
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(true);
  const [isEdited, setIsEdited] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLocalContent(content);
    setIsEdited(false);
  }, [content, path]);

  function handleCopy() {
    navigator.clipboard.writeText(localContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const val = e.target.value;
    setLocalContent(val);
    setIsEdited(val !== content);
    if (onContentChange) {
      onContentChange(val);
    }
  }

  function handleReset() {
    setLocalContent(content);
    setIsEdited(false);
    if (onContentChange) {
      onContentChange(content);
    }
  }

  function handleScroll() {
    if (textareaRef.current && lineNumsRef.current) {
      lineNumsRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  }

  const lines = localContent.split("\n");
  const filename = path.split("/").pop() || path;
  const language = getLanguageFromPath(path);
  const byteSize = new Blob([localContent]).size;

  return (
    <div className="code-container-card">
      {/* Right Container Header with Filename & Language Badges */}
      <div className="container-header-bar">
        <div className="container-header-badges">
          <div className="header-badge filename-badge" title={path}>
            <span className="badge-icon">📄</span>
            <span className="badge-text mono-text">{filename}</span>
          </div>
          <div className="header-badge language-badge">
            <span className="badge-icon">⚡</span>
            <span className="badge-text mono-text">{language}</span>
          </div>
          {isEdited && (
            <span className="header-badge edited-badge mono-text">
              ● Modified
            </span>
          )}
        </div>

        <div className="container-header-actions">
          <span className="code-meta mono-text">
            {lines.length} {lines.length === 1 ? "line" : "lines"} · {byteSize} B
          </span>

          {isEdited && (
            <button className="code-action-btn reset-btn" onClick={handleReset} type="button">
              Reset
            </button>
          )}

          <button
            className={`code-action-btn edit-toggle-btn ${isEditing ? "is-active" : ""}`}
            onClick={() => setIsEditing(!isEditing)}
            type="button"
          >
            {isEditing ? "✎ Edit Mode" : "👁 Read Only"}
          </button>

          <button className="code-action-btn copy-btn" onClick={handleCopy} type="button">
            {copied ? "✓ Copied" : "Copy Code"}
          </button>
        </div>
      </div>

      {/* Code Editor Body */}
      <div className="code-editor-body">
        {isLoading ? (
          <div className="code-loading mono-text">Loading file content...</div>
        ) : (
          <div className="editor-workspace">
            <div className="line-numbers-gutter" ref={lineNumsRef}>
              {lines.map((_, idx) => (
                <div key={idx} className="gutter-line-num mono-text">
                  {idx + 1}
                </div>
              ))}
            </div>

            {isEditing ? (
              <textarea
                ref={textareaRef}
                className="code-editor-textarea mono-text"
                value={localContent}
                onChange={handleChange}
                onScroll={handleScroll}
                spellCheck={false}
                placeholder="Enter code here..."
              />
            ) : (
              <pre className="code-pre-display" onScroll={handleScroll}>
                <code>
                  {lines.map((line, idx) => (
                    <div key={idx} className="code-display-line">
                      <span className="line-content">{line || " "}</span>
                    </div>
                  ))}
                </code>
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
