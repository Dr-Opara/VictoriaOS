"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Clipboard, Eraser, Mic, MicOff, Send } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { AICore, type AICoreState } from "@/components/ai-core/ai-core";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MarkdownMessage } from "@/components/ui/markdown";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";
import {
  getOrCreateSessionId,
  loadStoredChat,
  saveStoredChat,
  type StoredChatMessage,
} from "@/lib/local-chat";
import { cn } from "@/lib/utils";

type ChatStatus = "complete" | "thinking" | "speaking" | "error";

interface ChatMessage extends StoredChatMessage {
  status?: ChatStatus;
}

function makeId(): string {
  return crypto.randomUUID();
}

function welcomeMessage(): ChatMessage {
  return {
    id: "welcome",
    role: "assistant",
    content: "Hello, Dr. Opara. What can I help you with today?",
    createdAt: new Date().toISOString(),
    status: "complete",
  };
}

function prefersReducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([welcomeMessage()]);
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [voiceError, setVoiceError] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [sessionId, setSessionId] = useState("dashboard");
  const [hydrated, setHydrated] = useState(false);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const revealTimerRef = useRef<number | null>(null);
  const { toast } = useToast();

  const backend = useQuery({
    queryKey: ["system", "status"],
    queryFn: api.system.status,
    refetchInterval: 10_000,
  });

  useEffect(() => {
    const stored = loadStoredChat();
    const nextSessionId = getOrCreateSessionId();
    queueMicrotask(() => {
      setSessionId(nextSessionId);
      setMessages(stored.length ? stored : [welcomeMessage()]);
      setHydrated(true);
    });
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    saveStoredChat(messages.filter((message) => message.id !== "welcome"));
  }, [hydrated, messages]);

  useEffect(() => {
    const SpeechRecognitionCtor =
      window.webkitSpeechRecognition ?? window.SpeechRecognition;
    if (!SpeechRecognitionCtor) return;
    queueMicrotask(() => setSpeechSupported(true));

    const recognition = new SpeechRecognitionCtor();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0]?.[0]?.transcript ?? "";
      setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => {
      setListening(false);
      setVoiceError(true);
      window.setTimeout(() => setVoiceError(false), 3500);
      toast({
        title: "Microphone error",
        description: "Could not capture audio from this browser.",
        variant: "error",
      });
    };
    recognitionRef.current = recognition;
  }, [toast]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: prefersReducedMotion() ? "auto" : "smooth",
    });
  }, [messages, speaking]);

  useEffect(() => {
    return () => {
      if (revealTimerRef.current) window.clearInterval(revealTimerRef.current);
    };
  }, []);

  const revealResponse = useCallback((messageId: string, response: string, sources?: string[]) => {
    if (revealTimerRef.current) window.clearInterval(revealTimerRef.current);

    if (prefersReducedMotion()) {
      setMessages((prev) =>
        prev.map((message) =>
          message.id === messageId
            ? { ...message, content: response, sources, status: "complete" }
            : message,
        ),
      );
      setSpeaking(false);
      return;
    }

    setSpeaking(true);
    let cursor = 0;
    const step = Math.max(3, Math.ceil(response.length / 90));

    revealTimerRef.current = window.setInterval(() => {
      cursor = Math.min(response.length, cursor + step);
      setMessages((prev) =>
        prev.map((message) =>
          message.id === messageId
            ? {
                ...message,
                content: response.slice(0, cursor),
                sources,
                status: cursor >= response.length ? "complete" : "speaking",
              }
            : message,
        ),
      );

      if (cursor >= response.length && revealTimerRef.current) {
        window.clearInterval(revealTimerRef.current);
        revealTimerRef.current = null;
        setSpeaking(false);
      }
    }, 18);
  }, []);

  const mutation = useMutation({
    mutationFn: ({ command }: { command: string; assistantId: string }) =>
      api.think(command, sessionId),
    onSuccess: (data, variables) => {
      revealResponse(variables.assistantId, data.response, data.sources);
    },
    onError: (error, variables) => {
      setSpeaking(false);
      setMessages((prev) =>
        prev.map((message) =>
          message.id === variables.assistantId
            ? {
                ...message,
                content:
                  error instanceof Error
                    ? `I could not reach the backend: ${error.message}`
                    : "I could not reach the backend just now.",
                status: "error",
              }
            : message,
        ),
      );
      toast({
        title: "Victoria is unreachable",
        description: "The backend did not return a chat response.",
        variant: "error",
      });
    },
  });

  const handleSend = () => {
    const command = input.trim();
    if (!command || mutation.isPending) return;

    const assistantId = makeId();
    const now = new Date().toISOString();
    setMessages((prev) => [
      ...prev,
      { id: makeId(), role: "user", content: command, createdAt: now, status: "complete" },
      {
        id: assistantId,
        role: "assistant",
        content: "",
        createdAt: now,
        status: "thinking",
      },
    ]);
    setInput("");
    mutation.mutate({ command, assistantId });
  };

  const toggleMic = () => {
    if (!recognitionRef.current) {
      setVoiceError(true);
      window.setTimeout(() => setVoiceError(false), 3500);
      toast({
        title: "Voice input unavailable",
        description: "This browser does not expose SpeechRecognition.",
        variant: "error",
      });
      return;
    }

    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
      return;
    }

    recognitionRef.current.start();
    setListening(true);
  };

  const copyMessage = async (message: ChatMessage) => {
    await navigator.clipboard.writeText(message.content);
    toast({ title: "Copied response", variant: "success" });
  };

  const clearConversation = () => {
    setMessages([welcomeMessage()]);
    saveStoredChat([]);
    toast({ title: "Conversation cleared", variant: "success" });
  };

  const lastMessage = messages[messages.length - 1];
  const coreState: AICoreState =
    backend.isError || Boolean(backend.data && backend.data.status !== "online")
      ? "offline"
      : voiceError || lastMessage?.status === "error"
        ? "error"
        : listening
          ? "listening"
          : mutation.isPending
            ? "thinking"
            : speaking
              ? "speaking"
              : "idle";

  const coreLabel =
    coreState === "offline"
      ? "Backend offline"
      : coreState === "error"
        ? "Needs attention"
        : coreState === "thinking"
          ? "Thinking"
          : coreState === "speaking"
            ? "Speaking"
            : coreState === "listening"
              ? "Listening"
              : "Ready";

  return (
    <div className="mx-auto grid h-[calc(100vh-3.5rem)] max-w-6xl grid-cols-1 gap-4 px-4 py-5 md:px-8 lg:grid-cols-[1fr_260px]">
      <section className="glass flex min-h-0 flex-col rounded-lg" aria-label="Assistant chat">
        <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <div>
            <h1 className="text-lg font-semibold text-[var(--foreground)]">Assistant</h1>
            <p className="text-xs text-[var(--muted)]">
              Conversation history is kept locally on this dashboard.
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={clearConversation}
            aria-label="Clear conversation"
          >
            <Eraser className="size-4" />
          </Button>
        </div>

        <div
          ref={scrollRef}
          className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-5"
          aria-live="polite"
        >
          <AnimatePresence initial={false}>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                className={cn("flex", message.role === "user" ? "justify-end" : "justify-start")}
              >
                <div
                  className={cn(
                    "group max-w-[88%] rounded-lg px-4 py-3 text-sm leading-relaxed shadow-sm",
                    message.role === "user"
                      ? "bg-[var(--accent)] text-[#03181b]"
                      : "border border-[var(--border)] bg-white/[0.035] text-[var(--foreground)]",
                  )}
                >
                  {message.status === "thinking" && !message.content ? (
                    <div className="flex items-center gap-1 py-1" aria-label="Victoria is thinking">
                      {[0, 1, 2].map((dot) => (
                        <motion.span
                          key={dot}
                          className="size-1.5 rounded-full bg-[var(--accent)]"
                          animate={{ opacity: [0.3, 1, 0.3] }}
                          transition={{ repeat: Infinity, duration: 1, delay: dot * 0.15 }}
                        />
                      ))}
                    </div>
                  ) : (
                    <MarkdownMessage content={message.content} />
                  )}

                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {message.sources.map((source) => (
                        <Badge key={source} variant="outline">
                          {source}
                        </Badge>
                      ))}
                    </div>
                  )}

                  {message.role === "assistant" && message.content && (
                    <div className="mt-2 flex justify-end opacity-100 md:opacity-0 md:transition-opacity md:group-hover:opacity-100 md:group-focus-within:opacity-100">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => copyMessage(message)}
                      >
                        <Clipboard className="size-3.5" /> Copy
                      </Button>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        <div className="border-t border-[var(--border)] p-3">
          <div className="flex items-end gap-2">
            <Button
              type="button"
              variant={listening ? "default" : "outline"}
              size="icon"
              onClick={toggleMic}
              aria-pressed={listening}
              aria-label={listening ? "Stop voice input" : "Start voice input"}
            >
              {listening ? <Mic className="size-4" /> : <MicOff className="size-4" />}
            </Button>
            <Textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask Victoria anything..."
              className="max-h-36 min-h-11"
              aria-label="Message Victoria"
            />
            <Button
              type="button"
              size="icon"
              onClick={handleSend}
              disabled={mutation.isPending || !input.trim()}
              aria-label="Send message"
            >
              <Send className="size-4" />
            </Button>
          </div>
          {mutation.isError && (
            <p className="mt-2 text-xs text-[var(--danger)]">
              The last request failed. Your typed message stayed in the conversation history.
            </p>
          )}
        </div>
      </section>

      <aside className="glass flex flex-col items-center justify-between rounded-lg p-5 text-center lg:min-h-0">
        <AICore state={coreState} size={132} label={coreLabel} />
        <div className="mt-6 w-full space-y-3 text-left">
          <div className="rounded-lg border border-[var(--border)] bg-white/[0.025] p-3">
            <p className="text-xs text-[var(--muted)]">Backend</p>
            <p className="mt-1 text-sm font-medium text-[var(--foreground)]">
              {backend.isLoading
                ? "Checking"
                : backend.isError
                  ? "Offline"
                  : backend.data?.status ?? "Unknown"}
            </p>
          </div>
          <div className="rounded-lg border border-[var(--border)] bg-white/[0.025] p-3">
            <p className="text-xs text-[var(--muted)]">Voice input</p>
            <p className="mt-1 text-sm font-medium text-[var(--foreground)]">
              {speechSupported ? "Browser speech ready" : "Unavailable in this browser"}
            </p>
          </div>
          <div className="rounded-lg border border-[var(--border)] bg-white/[0.025] p-3">
            <p className="text-xs text-[var(--muted)]">Messages</p>
            <p className="mt-1 text-sm font-medium text-[var(--foreground)]">
              {messages.filter((message) => message.id !== "welcome").length}
            </p>
          </div>
        </div>
      </aside>
    </div>
  );
}
