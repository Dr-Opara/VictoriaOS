export const CHAT_HISTORY_KEY = "victoria.dashboard.chatHistory.v2";
export const CHAT_SESSION_KEY = "victoria.dashboard.sessionId.v2";

export type StoredChatRole = "user" | "assistant";

export interface StoredChatMessage {
  id: string;
  role: StoredChatRole;
  content: string;
  sources?: string[];
  createdAt: string;
}

export function getOrCreateSessionId(): string {
  const existing = window.localStorage.getItem(CHAT_SESSION_KEY);
  if (existing) return existing;

  const sessionId = `dashboard-${crypto.randomUUID()}`;
  window.localStorage.setItem(CHAT_SESSION_KEY, sessionId);
  return sessionId;
}

export function loadStoredChat(): StoredChatMessage[] {
  const raw = window.localStorage.getItem(CHAT_HISTORY_KEY);
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw) as StoredChatMessage[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveStoredChat(messages: StoredChatMessage[]): void {
  window.localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(messages.slice(-80)));
}
