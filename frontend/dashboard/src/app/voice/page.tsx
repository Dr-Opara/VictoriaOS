"use client";

import { motion } from "framer-motion";
import { Mic, MicOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type ListenState = "idle" | "listening" | "unsupported" | "denied";

export default function VoicePage() {
  const [state, setState] = useState<ListenState>("idle");
  const [transcript, setTranscript] = useState("");
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    const SpeechRecognitionCtor =
      (window as typeof window & { webkitSpeechRecognition?: typeof SpeechRecognition })
        .webkitSpeechRecognition ?? window.SpeechRecognition;

    if (!SpeechRecognitionCtor) {
      // One-time browser capability check at mount.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setState("unsupported");
      return;
    }

    const recognition = new SpeechRecognitionCtor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const text = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? "")
        .join(" ");
      setTranscript(text);
    };

    recognition.onerror = () => setState("denied");
    recognition.onend = () => setState((current) => (current === "listening" ? "idle" : current));

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
    };
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) return;

    if (state === "listening") {
      recognitionRef.current.stop();
      setState("idle");
    } else {
      setTranscript("");
      recognitionRef.current.start();
      setState("listening");
    }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center gap-8 px-4 py-16 text-center">
      <div>
        <h1 className="text-xl font-semibold text-neutral-50">Voice</h1>
        <p className="mt-1 text-sm text-neutral-500">Say &ldquo;Hello Victoria&rdquo; to begin.</p>
      </div>

      <button
        onClick={toggleListening}
        disabled={state === "unsupported"}
        className="relative flex h-32 w-32 items-center justify-center rounded-full border border-white/10 bg-neutral-900 transition-colors disabled:opacity-40"
      >
        {state === "listening" && (
          <motion.span
            className="absolute inset-0 rounded-full bg-white/10"
            animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ repeat: Infinity, duration: 1.8 }}
          />
        )}
        {state === "listening" ? (
          <Mic className="size-10 text-white" />
        ) : (
          <MicOff className="size-10 text-neutral-500" />
        )}
      </button>

      <p className="text-sm text-neutral-500">
        {state === "unsupported" && "This browser doesn't support microphone speech recognition."}
        {state === "denied" && "Microphone access was denied."}
        {state === "idle" && "Tap the microphone to start listening."}
        {state === "listening" && "Listening…"}
      </p>

      <Card className="w-full text-left">
        <CardHeader>
          <CardTitle>Live transcript</CardTitle>
          <CardDescription>
            Browser speech recognition, for local testing. Production voice runs through the
            VictoriaOS voice pipeline (wake word, VAD, OpenAI STT/TTS, conversation mode) —
            see <code>POST /voice/command</code>.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="min-h-16 text-sm text-neutral-300">
            {transcript || "Nothing yet — start speaking."}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
