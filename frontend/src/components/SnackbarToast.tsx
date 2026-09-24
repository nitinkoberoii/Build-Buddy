import React, { useEffect } from "react";

interface SnackbarToastProps {
  title?: string;
  message: string;
  type?: "warning" | "error" | "info" | "success";
  durationMs?: number;
  onClose: () => void;
}

export const SnackbarToast: React.FC<SnackbarToastProps> = ({
  title = "Notice",
  message,
  type = "warning",
  durationMs = 6000,
  onClose,
}) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, durationMs);
    return () => clearTimeout(timer);
  }, [durationMs, onClose]);

  function getIcon() {
    switch (type) {
      case "error":
        return "🚨";
      case "warning":
        return "⚠️";
      case "success":
        return "✓";
      default:
        return "ℹ️";
    }
  }

  return (
    <div className={`snackbar-toast snackbar-${type}`}>
      <div className="snackbar-content">
        <span className="snackbar-icon">{getIcon()}</span>
        <div className="snackbar-text">
          <span className="snackbar-title">{title}</span>
          <span className="snackbar-message">{message}</span>
        </div>
        <button
          className="snackbar-close"
          onClick={onClose}
          type="button"
          aria-label="Close notification"
        >
          ✕
        </button>
      </div>

      {/* Bottom progress bar spanning durationMs seconds */}
      <div
        className="snackbar-progress-bar"
        style={{ animationDuration: `${durationMs}ms` }}
      />
    </div>
  );
};
