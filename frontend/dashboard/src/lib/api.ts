const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new ApiError(body || response.statusText, response.status);
  }

  return response.json() as Promise<T>;
}

export interface ThinkResponse {
  assistant: string;
  response: string;
}

export interface MemoryItem {
  key: string;
  value: string;
  created_at: string;
}

export interface TaskItem {
  id: number;
  title: string;
  description: string;
  status: "pending" | "completed";
  due_at: string | null;
  created_at: string;
  completed_at: string | null;
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

export const api = {
  think: (command: string, sessionId = "dashboard") =>
    request<ThinkResponse>(
      `/think?command=${encodeURIComponent(command)}&session_id=${encodeURIComponent(sessionId)}`,
    ),

  memory: {
    list: (query?: string) =>
      request<{ memories: MemoryItem[] }>(
        `/memory${query ? `?query=${encodeURIComponent(query)}` : ""}`,
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
  },

  tasks: {
    list: (status?: string) =>
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
  },

  email: {
    unread: () =>
      request<{ configured: boolean; error?: string; messages: EmailMessage[] }>(
        "/email/unread",
      ),
  },

  system: {
    status: () => request<SystemStatus>("/system/status"),
    usage: () => request<SystemUsage>("/system/usage"),
    logs: (limit = 200) => request<{ lines: string[] }>(`/system/logs?limit=${limit}`),
  },
};
