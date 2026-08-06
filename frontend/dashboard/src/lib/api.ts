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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
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
  sources?: string[];
}

export interface MemoryItem {
  key: string;
  value: string;
  created_at: string;
}

export type TaskPriority = "high" | "medium" | "low" | null;

export interface TaskItem {
  id: number;
  title: string;
  description: string;
  status: "pending" | "completed";
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

export interface CalendarEventItem {
  id: number;
  title: string;
  description: string;
  location: string;
  start_time: string;
  end_time: string;
}

export interface WeatherReport {
  configured: boolean;
  error?: string;
  location?: string;
  description?: string;
  temperature_f?: string;
  feels_like_f?: string;
  humidity_percent?: string;
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
    prioritize: () =>
      request<{ plans: TaskPlan[] }>("/tasks/prioritize", { method: "POST" }),
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

  calendar: {
    today: () => request<{ events: CalendarEventItem[] }>("/calendar/today"),
    upcoming: (limit = 10) =>
      request<{ events: CalendarEventItem[] }>(`/calendar/upcoming?limit=${limit}`),
    create: (event: {
      title: string;
      start_time: string;
      end_time: string;
      description?: string;
      location?: string;
    }) =>
      request<CalendarEventItem>("/calendar/events", {
        method: "POST",
        body: JSON.stringify(event),
      }),
    cancel: (id: number) =>
      request<{ status: string; id: number }>(`/calendar/events/${id}`, { method: "DELETE" }),
  },

  weather: {
    current: () => request<WeatherReport>("/weather/current"),
  },

  briefing: {
    get: () => request<{ briefing: string }>("/briefing"),
    voiceUrl: () => `${API_BASE_URL}/briefing/voice`,
  },

  knowledge: {
    list: () => request<{ documents: DocumentSummary[] }>("/knowledge/documents"),
    upload: async (file: File): Promise<DocumentSummary> => {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${API_BASE_URL}/knowledge/documents`, {
        method: "POST",
        headers: API_KEY ? { "X-API-Key": API_KEY } : undefined,
        body: formData,
      });
      if (!response.ok) {
        const body = await response.text().catch(() => "");
        throw new ApiError(body || response.statusText, response.status);
      }
      return response.json();
    },
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
