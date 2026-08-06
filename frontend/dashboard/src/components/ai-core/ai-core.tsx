"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { AlertTriangle, WifiOff } from "lucide-react";

import { cn } from "@/lib/utils";

export type AICoreState = "idle" | "listening" | "thinking" | "speaking" | "offline" | "error";

const STATE_COPY: Record<AICoreState, string> = {
  idle: "Idle",
  listening: "Listening",
  thinking: "Thinking",
  speaking: "Speaking",
  offline: "Offline",
  error: "Error",
};

const STATE_COLOR: Record<AICoreState, string> = {
  idle: "#22e5ee",
  listening: "#3ce8a0",
  thinking: "#9b8cff",
  speaking: "#ffcc66",
  offline: "#5b6b78",
  error: "#ff5c6c",
};

interface AICoreProps {
  state: AICoreState;
  size?: number;
  label?: string;
  className?: string;
}

function repeat(shouldReduceMotion: boolean | null, active = true) {
  return shouldReduceMotion || !active ? 0 : Infinity;
}

export function AICore({ state, size = 140, label, className }: AICoreProps) {
  const shouldReduceMotion = useReducedMotion();
  const color = STATE_COLOR[state];
  const isOffline = state === "offline";
  const isError = state === "error";
  const isInteractive = state === "listening" || state === "thinking" || state === "speaking";

  return (
    <div className={cn("flex flex-col items-center gap-3", className)}>
      <div
        className="relative flex items-center justify-center"
        style={{ width: size, height: size }}
        role="img"
        aria-live="polite"
        aria-label={`Victoria AI core: ${STATE_COPY[state]}`}
      >
        <motion.div
          className="absolute inset-0 rounded-full blur-2xl"
          style={{ background: color }}
          animate={{
            opacity: isOffline ? 0.06 : isError ? 0.32 : isInteractive ? 0.26 : 0.16,
            scale: state === "idle" ? [1, 1.04, 1] : state === "listening" ? [1, 1.12, 1] : 1,
          }}
          transition={{
            repeat: repeat(shouldReduceMotion, state === "idle" || state === "listening"),
            duration: state === "listening" ? 1.2 : 3,
          }}
        />

        <div
          className="absolute inset-1 rounded-full border"
          style={{ borderColor: isOffline ? "var(--border)" : color }}
        />

        <AnimatePresence>
          {state === "thinking" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1, rotate: 360 }}
              exit={{ opacity: 0 }}
              transition={{
                rotate: {
                  repeat: repeat(shouldReduceMotion),
                  duration: 1.4,
                  ease: "linear",
                },
              }}
              className="absolute inset-2 rounded-full"
              style={{
                background: `conic-gradient(from 0deg, transparent, ${color}, transparent 58%)`,
                maskImage: "radial-gradient(closest-side, transparent 76%, black 78%)",
                WebkitMaskImage: "radial-gradient(closest-side, transparent 76%, black 78%)",
              }}
            />
          )}
        </AnimatePresence>

        <AnimatePresence>
          {state === "listening" && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: [0.7, 0.15, 0.7], scale: [1, 1.32, 1] }}
              exit={{ opacity: 0 }}
              transition={{ repeat: repeat(shouldReduceMotion), duration: 1.2 }}
              className="absolute inset-3 rounded-full border-2"
              style={{ borderColor: color }}
            />
          )}
        </AnimatePresence>

        <motion.div
          className={cn(
            "relative flex h-[62%] w-[62%] items-center justify-center rounded-full border",
            !isOffline && "glow-cyan",
          )}
          style={{
            borderColor: isOffline ? "var(--border)" : color,
            background: `radial-gradient(circle at 35% 30%, color-mix(in srgb, ${color} 88%, white), color-mix(in srgb, ${color} 42%, #05070a))`,
            filter: isOffline ? "grayscale(0.9)" : undefined,
          }}
          animate={
            shouldReduceMotion
              ? { scale: 1 }
              : state === "idle"
                ? { scale: [1, 1.025, 1] }
                : state === "speaking"
                  ? { scale: [1, 1.08, 0.98, 1.05, 1] }
                  : { scale: 1 }
          }
          transition={{
            repeat: repeat(shouldReduceMotion, state === "idle" || state === "speaking"),
            duration: state === "speaking" ? 0.72 : 2.8,
          }}
        >
          {isOffline && <WifiOff className="size-6 text-neutral-300" />}
          {isError && <AlertTriangle className="size-6 text-white" />}
        </motion.div>

        {(state === "speaking" || state === "listening") && (
          <div className="absolute -bottom-1 flex h-6 items-end gap-0.5" aria-hidden="true">
            {[0, 1, 2, 3, 4, 5, 6].map((bar) => (
              <motion.span
                key={bar}
                className="w-0.5 rounded-full"
                style={{ background: color }}
                animate={
                  shouldReduceMotion
                    ? { height: 8 }
                    : { height: state === "speaking" ? [5, 18, 7, 14, 5] : [4, 10, 5] }
                }
                transition={{
                  repeat: repeat(shouldReduceMotion),
                  duration: state === "speaking" ? 0.78 : 1.1,
                  delay: bar * 0.06,
                }}
              />
            ))}
          </div>
        )}
      </div>

      <span className="text-xs font-medium text-[var(--muted)]">{label ?? STATE_COPY[state]}</span>
    </div>
  );
}
