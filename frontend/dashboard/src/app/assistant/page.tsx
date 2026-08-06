"use client";

import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Mic, MicOff, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { AICore, type AICoreState } from "@/components/ai-core/ai-core";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hello, Dr. Opara. What can I help you with today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    const SpeechRecognitionCtor =
      (window as typeof window & { webkitSpeechRecognition?: typeof SpeechRecognition })
        .webkitSpeechRecognition ?? window.SpeechRecognition;
    if (!SpeechRecognitionCtor) return;

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
      toast({ title: "Microphone error", description: "Could not capture audio.", variant: "error" });
    };
    recognitionRef.current = recognition;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const mutation = useMutation({
    mutationFn: (command: string) => api.think(command),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: data.response, sources: data.sources },
      ]);
      requestAnimationFrame(() => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
      });
    },
    onError: () => {
      toast({
        title: "Victoria is unreachable",
        description: "Couldn't reach the backend just now.",
        variant: "error",
      });
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "I couldn't reach the backend just now. Please try again.",
        },
      ]);
    },
  });

  const coreState: AICoreState = mutation.isPending
    ? "thinking"
    : listening
      ? "listening"
      : "idle";

  const handleSend = () => {
    const command = input.trim();
    if (!command || mutation.isPending) return;

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: command }]);
    setInput("");
    mutation.mutate(command);
  };

  const toggleMic = () => {
    if (!recognitionRef.current) {
      toast({
        title: "Voice input unavailable",
        description: "This browser doesn't support speech recognition.",
        variant: "error",
      });
      return;
    }
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      recognitionRef.current.start();
      setListening(true);
    }
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-3.5rem)] max-w-3xl flex-col px-4 py-6 md:px-8">
      <div className="mb-4 flex items-center justify-center">
        <AICore state={coreState} size={96} />
      </div>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto pb-4">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn("flex", message.role === "user" ? "justify-end" : "justify-start")}
            >
              <div
                className={cn(
                  "max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                  message.role === "user"
                    ? "bg-[var(--accent)] text-[#03181b]"
                    : "glass text-[var(--foreground)]",
                )}
              >
                {message.content}
                {message.sources && message.sources.length > 0 && (
                  <p className="mt-2 text-xs opacity-70">Sources: {message.sources.join(", ")}</p>
                )}
              </div>
            </motion.div>
          ))}
          {mutation.isPending && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
              <div className="glass flex items-center gap-1 rounded-2xl px-4 py-3">
                {[0, 1, 2].map((dot) => (
                  <motion.span
                    key={dot}
                    className="size-1.5 rounded-full bg-[var(--accent)]"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ repeat: Infinity, duration: 1, delay: dot * 0.15 }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="flex items-end gap-2 border-t border-[var(--border)] pt-4">
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
          placeholder="Ask Victoria anything…"
          className="min-h-11"
        />
        <Button size="icon" onClick={handleSend} disabled={mutation.isPending || !input.trim()}>
          <Send className="size-4" />
        </Button>
      </div>
    </div>
  );
}
