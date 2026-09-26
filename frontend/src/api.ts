import {
  GenerationResponse,
  GenerationEvent,
  FileNode,
  FileContentResponse,
} from "./types";

const API_BASE = "/api";

export async function createGeneration(
  prompt: string,
  model?: string
): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE}/generations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt, model }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to start generation run");
  }

  return response.json();
}

export async function refineGeneration(
  id: string,
  prompt: string
): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE}/generations/${id}/refine`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to submit refinement edit request");
  }

  return response.json();
}

export async function getGeneration(id: string): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE}/generations/${id}`);
  if (!response.ok) {
    throw new Error("Failed to fetch generation status");
  }
  return response.json();
}

export async function getFileTree(id: string): Promise<FileNode[]> {
  const response = await fetch(`${API_BASE}/generations/${id}/files`);
  if (!response.ok) {
    throw new Error("Failed to fetch project files");
  }
  return response.json();
}

export async function getFileContent(
  id: string,
  path: string
): Promise<FileContentResponse> {
  const encodedPath = path
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  const response = await fetch(`${API_BASE}/generations/${id}/files/${encodedPath}`);
  if (!response.ok) {
    throw new Error(`Failed to read file: ${path}`);
  }
  return response.json();
}

export async function cancelGeneration(id: string): Promise<boolean> {
  const response = await fetch(`${API_BASE}/generations/${id}/cancel`, {
    method: "POST",
  });
  if (!response.ok) {
    return false;
  }
  const data = await response.json();
  return data.cancelled;
}

export function getDownloadUrl(id: string): string {
  return `${API_BASE}/generations/${id}/download`;
}

export function subscribeToEvents(
  id: string,
  onEvent: (event: GenerationEvent) => void,
  onError?: (error: any) => void
): () => void {
  const eventSource = new EventSource(`${API_BASE}/generations/${id}/events`);

  eventSource.onmessage = (e) => {
    try {
      const parsed: GenerationEvent = JSON.parse(e.data);
      onEvent(parsed);
    } catch (err) {
      console.error("Failed to parse SSE event payload:", err);
    }
  };

  eventSource.onerror = (err) => {
    if (onError) onError(err);
    eventSource.close();
  };

  return () => {
    eventSource.close();
  };
}
