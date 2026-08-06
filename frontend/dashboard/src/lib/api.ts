const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function apiHeaders(includeJson = true): HeadersInit {
  return {
    ...(includeJson ? { "Content-Type": "application/json" } : {}),
    ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
  };
}

async function parseError(response: Response): Promise<string> {
  const body = await response.text().catch(() => "");
  if (!body) return response.statusText;

  try {
    const parsed = JSON.parse(body) as { detail?: string; message?: string };
    return parsed.detail ?? parsed.message ?? body;
  } catch {
    return body;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...apiHeaders(),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }

  return response.json() as Promise<T>;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface ThinkResponse {
  assistant: string;
  response: string;
  sources?: string[];
}

export interface MemoryItem {
  key: string;
  value: string;
  created_at: string;
}

export type TaskPriority = "high" | "medium" | "low" | null;
export type TaskStatus = "pending" | "completed";

export interface TaskItem {
  id: number;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_at: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface TaskPlan {
  task_id: number;
  priority: TaskPriority;
  follow_up: string;
}

export interface EmailMessage {
  sender: string;
  subject: string;
  date: string;
  preview: string;
}

export interface SystemStatus {
  status: string;
  uptime_seconds: number;
  version: string;
  environment: string;
  model: string;
}

export interface SystemUsage {
  conversation_turns: number;
  memories_stored: number;
  tasks_total: number;
  tasks_pending: number;
}

export interface DocumentSummary {
  id: number;
  filename: string;
  content_type: string;
  char_count: number;
  chunk_count: number;
}

export interface KnowledgeSearchResult {
  chunk_id: number;
  document_id: number;
  text: string;
  score: number;
}

export interface VoiceConnectResponse {
  session_id: string;
  wake_word: string;
  sample_rate: number;
  sample_width_bytes: number;
  channels: number;
  encoding: string;
}

export interface UploadOptions {
  onProgress?: (percent: number) => void;
}

function uploadDocument(file: File, options?: UploadOptions): Promise<DocumentSummary> {
  const formData = new FormData();
  formData.append("file", file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}/knowledge/documents`);

    if (API_KEY) {
      xhr.setRequestHeader("X-API-Key", API_KEY);
    }

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable || !options?.onProgress) return;
      options.onProgress(Math.round((event.loaded / event.total) * 100));
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        options?.onProgress?.(100);
        resolve(JSON.parse(xhr.responseText) as DocumentSummary);
        return;
      }

      let message = xhr.statusText || "Upload failed";
      try {
        const parsed = JSON.parse(xhr.responseText) as { detail?: string; message?: string };
        message = parsed.detail ?? parsed.message ?? message;
      } catch {
        if (xhr.responseText) message = xhr.responseText;
      }
      reject(new ApiError(message, xhr.status));
    };

    xhr.onerror = () => reject(new ApiError("Network error while uploading document.", 0));
    xhr.send(formData);
  });
}

export const api = {
  root: () =>
    request<{ assistant: string; status: string; owner: string; environment: string }>("/"),

  health: () => request<HealthResponse>("/health"),

  think: (command: string, sessionId = "dashboard") =>
    request<ThinkResponse>(
      `/think?command=${encodeURIComponent(command)}&session_id=${encodeURIComponent(sessionId)}`,
    ),

  memory: {
    list: (query?: string, limit = 20) =>
      request<{ memories: MemoryItem[] }>(
        `/memory?limit=${limit}${query ? `&query=${encodeURIComponent(query)}` : ""}`,
      ),
    remember: (key: string, value: string) =>
      request<{ status: string; key: string; value: string }>("/remember", {
        method: "POST",
        body: JSON.stringify({ key, value }),
      }),
    forget: (key: string) =>
      request<{ status: string; key: string; removed: number }>("/forget", {
        method: "POST",
        body: JSON.stringify({ key }),
      }),
    replace: async (key: string, value: string) => {
      await api.memory.forget(key);
      return api.memory.remember(key, value);
    },
  },

  tasks: {
    list: (status?: TaskStatus) =>
      request<{ tasks: TaskItem[] }>(`/tasks${status ? `?status=${status}` : ""}`),
    create: (title: string, description = "") =>
      request<TaskItem>("/tasks", {
        method: "POST",
        body: JSON.stringify({ title, description }),
      }),
    complete: (id: number) =>
      request<TaskItem>(`/tasks/${id}/complete`, { method: "POST" }),
    remove: (id: number) =>
      request<{ status: string; id: number }>(`/tasks/${id}`, { method: "DELETE" }),
    replace: async (task: TaskItem, title: string, description: string) => {
      const replacement = await api.tasks.create(title, description);
      if (task.status === "completed") {
        await api.tasks.complete(replacement.id);
      }
      await api.tasks.remove(task.id);
      return replacement;
    },
    prioritize: () =>
      request<{ plans: TaskPlan[] }>("/tasks/prioritize", { method: "POST" }),
  },

  email: {
    unread: (limit = 20) =>
      request<{ configured: boolean; error?: string; messages: EmailMessage[] }>(
        `/email/unread?limit=${limit}`,
      ),
    summarizeUnread: (sessionId = "dashboard-email") =>
      api.think("Summarize my unread Yahoo Mail.", sessionId),
  },

  system: {
    status: () => request<SystemStatus>("/system/status"),
    usage: () => request<SystemUsage>("/system/usage"),
    logs: (limit = 200) => request<{ lines: string[] }>(`/system/logs?limit=${limit}`),
  },

  briefing: {
    get: () => request<{ briefing: string }>("/briefing"),
    voiceUrl: () => `${API_BASE_URL}/briefing/voice`,
  },

  voice: {
    connect: () => request<VoiceConnectResponse>("/voice/connect"),
  },

  knowledge: {
    list: () => request<{ documents: DocumentSummary[] }>("/knowledge/documents"),
    upload: uploadDocument,
    remove: (id: number) =>
      request<{ status: string; id: number }>(`/knowledge/documents/${id}`, {
        method: "DELETE",
      }),
    search: (q: string, limit = 5) =>
      request<{ results: KnowledgeSearchResult[] }>(
        `/knowledge/search?q=${encodeURIComponent(q)}&limit=${limit}`,
      ),
    ask: (question: string, limit = 5) =>
      request<{ answer: string; sources: string[] }>("/knowledge/ask", {
        method: "POST",
        body: JSON.stringify({ question, limit }),
      }),
  },
};
