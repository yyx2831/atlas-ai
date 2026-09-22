export interface User {
  id: number;
  email: string;
  role: "admin" | "viewer";
}
export interface Device {
  id: number;
  name: string;
  device_type: "router" | "switch" | "camera";
  ip: string;
}
export interface Alarm {
  id: number;
  device_id: number;
  level: string;
  created_at: string;
}
export interface Document {
  id: string;
  filename: string;
  product: string;
  version: string;
  status: string;
  error: string;
  created_at: string;
  index_key: string;
}
export interface Citation {
  id: string;
  document_id: string;
  filename: string;
  page: number;
  content: string;
  score: number;
  label?: string;
}
export interface Message {
  id?: number;
  role: string;
  content: string;
  status: string;
  citations: Citation[];
  metrics?: Record<string, unknown>;
}
export interface Conversation {
  id: string;
  title: string;
  created_at: string;
}
export interface Step {
  tool: string;
  result: { ok: boolean; data?: unknown; error?: string };
  duration_ms: number;
  transport: string;
}
export interface AgentRun {
  id: string;
  question?: string;
  status: string;
  answer: string;
  steps: Step[];
}
export interface SystemInfo {
  llm_mode: string;
  model: string;
  embedding_mode: string;
  reranker: string;
  vector_store: string;
  index_key: string;
  max_upload_mb: number;
}
