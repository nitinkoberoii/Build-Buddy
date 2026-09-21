import React, { useState } from "react";
import { FileNode } from "../types";

interface FileTreeProps {
  nodes: FileNode[];
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
}

function getFileIcon(name: string, type: "file" | "directory"): string {
  if (type === "directory") return "📁";
  const ext = name.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "html":
      return "🌐";
    case "css":
      return "🎨";
    case "js":
    case "ts":
    case "jsx":
    case "tsx":
      return "⚡";
    case "json":
      return "⚙️";
    case "md":
      return "📝";
    default:
      return "📄";
  }
}

interface TreeNodeProps {
  node: FileNode;
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
}

const TreeNode: React.FC<TreeNodeProps> = ({ node, selectedPath, onSelectFile }) => {
  const [isOpen, setIsOpen] = useState(true);
  const isSelected = selectedPath === node.path;
  const icon = getFileIcon(node.name, node.type);

  if (node.type === "directory") {
    return (
      <div className="tree-dir">
        <button
          className="tree-item tree-dir-btn"
          type="button"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="tree-arrow">{isOpen ? "▼" : "▶"}</span>
          <span className="tree-icon">{icon}</span>
          <span className="tree-name">{node.name}</span>
        </button>
        {isOpen && node.children && (
          <div className="tree-children">
            {node.children.map((child) => (
              <TreeNode
                key={child.path}
                node={child}
                selectedPath={selectedPath}
                onSelectFile={onSelectFile}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <button
      className={`tree-item tree-file-btn ${isSelected ? "is-selected" : ""}`}
      type="button"
      onClick={() => onSelectFile(node.path)}
    >
      <span className="tree-icon">{icon}</span>
      <span className="tree-name">{node.name}</span>
    </button>
  );
};

export const FileTree: React.FC<FileTreeProps> = ({
  nodes,
  selectedPath,
  onSelectFile,
}) => {
  if (nodes.length === 0) {
    return <div className="tree-empty text-muted">No files generated yet.</div>;
  }

  return (
    <div className="file-tree">
      {nodes.map((node) => (
        <TreeNode
          key={node.path}
          node={node}
          selectedPath={selectedPath}
          onSelectFile={onSelectFile}
        />
      ))}
    </div>
  );
};
