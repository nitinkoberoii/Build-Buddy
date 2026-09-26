export type GenerationState =
  | "queued"
  | "planning"
  | "architecting"
  | "coding"
  | "completed"
  | "failed"
  | "cancelled";

export interface PlanFile {
  path: string;
  purpose: string;
}

export interface Plan {
  name: string;
  description: string;
  techstack: string;
  features: string[];
  files: PlanFile[];
}

export interface ImplementationTask {
  filepath: string;
  task_description: string;
}

export interface TaskPlan {
  implementation_steps: ImplementationTask[];
  plan?: Plan;
}

export interface ThreadMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  status?: "completed" | "refining" | "failed";
  files_changed?: string[];
}

export interface GenerationResponse {
  id: string;
  prompt: string;
  model: string;
  state: GenerationState;
  created_at: string;
  updated_at: string;
  plan?: Plan;
  task_plan?: TaskPlan;
  error?: string;
  messages?: ThreadMessage[];
}

export interface GenerationEvent {
  id: string;
  generation_id: string;
  stage: string;
  message: string;
  timestamp: string;
  data?: Record<string, any>;
}

export interface FileNode {
  name: string;
  path: string;
  type: "file" | "directory";
  size?: number;
  children?: FileNode[];
}

export interface FileContentResponse {
  path: string;
  content: string;
  size: number;
}
