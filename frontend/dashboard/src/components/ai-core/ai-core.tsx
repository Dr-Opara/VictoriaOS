"use client";

import { AnimatePresence, motion } from "framer-motion";
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
  listening: "#5cf2ff",
  thinking: "#22e5ee",
  speaking: "#5cf2ff",
  offline: "#5b6b78",
  error: "#ff5c6c",
};

interface AICoreProps {
  state: AICoreState;
  size?: number;
  label?: string;
  className?: string;
}

/**
 * VictoriaOS's animated core visual - an original design (concentric
 * glowing rings + a reactive waveform), not modeled on any specific
 * existing product's assistant orb.
 */
export function AICore({ state, size = 140, label, className }: AICoreProps) {
  const color = STATE_COLOR[state];

  return (
    <div className={cn("flex flex-col items-center gap-3", className)}>
      <div
        className="relative flex items-center justify-center"
        style={{ width: size, height: size }}
        role="img"
        aria-label={`Victoria AI core: ${STATE_COPY[state]}`}
      >
        {/* Outer ambient glow */}
        <motion.div
          className="absolute inset-0 rounded-full blur-2xl"
          style={{ background: color }}
          animate={{
            opacity: state === "offline" ? 0.08 : state === "error" ? 0.35 : 0.28,
            scale: state === "idle" ? [1, 1.08, 1] : 1,
          }}
          transition={{ repeat: state === "idle" ? Infinity : 0, duration: 3 }}
        />

        {/* Thinking: rotating conic ring */}
        <AnimatePresence>
          {state === "thinking" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1, rotate: 360 }}
              exit={{ opacity: 0 }}
              transition={{ rotate: { repeat: Infinity, duration: 1.6, ease: "linear" } }}
              className="absolute inset-2 rounded-full"
              style={{
                background: `conic-gradient(from 0deg, transparent, ${color}, transparent 60%)`,
                maskImage: "radial-gradient(closest-side, transparent 78%, black 80%)",
                WebkitMaskImage: "radial-gradient(closest-side, transparent 78%, black 80%)",
              }}
            />
          )}
        </AnimatePresence>

        {/* Listening / speaking: pulsing ring */}
        <AnimatePresence>
          {(state === "listening" || state === "speaking") && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: [0.6, 0, 0.6], scale: [1, 1.35, 1] }}
              exit={{ opacity: 0 }}
              transition={{ repeat: Infinity, duration: state === "listening" ? 1.4 : 0.9 }}
              className="absolute inset-3 rounded-full border-2"
              style={{ borderColor: color }}
            />
          )}
        </AnimatePresence>

        {/* Core sphere */}
        <motion.div
          className={cn(
            "relative flex h-[62%] w-[62%] items-center justify-center rounded-full",
            state !== "offline" && "glow-cyan",
          )}
          style={{
            background: `radial-gradient(circle at 35% 30%, color-mix(in srgb, ${color} 90%, white), color-mix(in srgb, ${color} 40%, black))`,
          }}
          animate={
            state === "idle"
              ? { scale: [1, 1.04, 1] }
              : state === "speaking"
                ? { scale: [1, 1.1, 0.97, 1.06, 1] }
                : { scale: 1 }
          }
          transition={{
            repeat: state === "idle" || state === "speaking" ? Infinity : 0,
            duration: state === "speaking" ? 0.7 : 2.8,
          }}
        >
          {state === "offline" && <WifiOff className="size-6 text-neutral-300" />}
          {state === "error" && <AlertTriangle className="size-6 text-white" />}
        </motion.div>

        {/* Speaking waveform bars */}
        {state === "speaking" && (
          <div className="absolute -bottom-1 flex items-end gap-0.5">
            {[0, 1, 2, 3, 4].map((bar) => (
              <motion.span
                key={bar}
                className="w-0.5 rounded-full"
                style={{ background: color }}
                animate={{ height: [4, 14, 6, 18, 4] }}
                transition={{ repeat: Infinity, duration: 0.8, delay: bar * 0.08 }}
              />
            ))}
          </div>
        )}
      </div>

      <span className="text-xs font-medium tracking-wide text-[var(--muted)]">
        {label ?? STATE_COPY[state]}
      </span>
    </div>
  );
}
