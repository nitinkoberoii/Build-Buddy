import React, { useState } from "react";

interface CodeViewerProps {
  path: string;
  content: string;
  isLoading?: boolean;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  path,
  content,
  isLoading,
}) => {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const lines = content.split("\n");

  return (
    <div className="code-viewer-panel">
      <div className="code-viewer-header">
        <div className="code-path-info">
          <span className="code-path mono-text">{path}</span>
          <span className="code-meta mono-text">
            {lines.length} lines · {content.length} bytes
          </span>
        </div>
        <button className="copy-btn" onClick={handleCopy} type="button">
          {copied ? "✓ Copied" : "Copy Code"}
        </button>
      </div>

      <div className="code-viewer-body">
        {isLoading ? (
          <div className="code-loading mono-text">Loading file content...</div>
        ) : (
          <pre className="code-pre">
            <code>
              {lines.map((line, idx) => (
                <div key={idx} className="code-line">
                  <span className="line-num mono-text">{idx + 1}</span>
                  <span className="line-text">{line || " "}</span>
                </div>
              ))}
            </code>
          </pre>
        )}
      </div>
    </div>
  );
};
