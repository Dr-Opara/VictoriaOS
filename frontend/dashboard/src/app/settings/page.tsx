"use client";

import { useQuery } from "@tanstack/react-query";
import { Bot, Moon, ScrollText, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    // Standard next-themes SSR-safe pattern: the resolved theme is only known
    // after mount, so we avoid rendering theme-dependent UI until then.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  const status = useQuery({ queryKey: ["system", "status"], queryFn: api.system.status });
  const usage = useQuery({ queryKey: ["system", "usage"], queryFn: api.system.usage });
  const logs = useQuery({
    queryKey: ["system", "logs"],
    queryFn: () => api.system.logs(100),
    refetchInterval: 10_000,
  });

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 md:px-8">
      <h1 className="text-xl font-semibold text-[var(--foreground)]">Settings</h1>
      <p className="mb-6 text-sm text-[var(--muted)]">Preferences for the Victoria dashboard.</p>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Dark luxury by default, matching Victoria&apos;s aesthetic.</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-2">
          {mounted && (
            <>
              <Button
                variant={theme === "dark" ? "default" : "outline"}
                size="sm"
                onClick={() => setTheme("dark")}
              >
                <Moon className="size-4" /> Dark
              </Button>
              <Button
                variant={theme === "light" ? "default" : "outline"}
                size="sm"
                onClick={() => setTheme("light")}
              >
                <Sun className="size-4" /> Light
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Backend</CardTitle>
          <CardDescription>Connection details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-1 text-sm text-[var(--muted)]">
          <p>
            API URL: <code>{process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}</code>
          </p>
          <p>Environment: {status.data?.environment ?? "unknown"}</p>
          <p>Version: {status.data?.version ?? "unknown"}</p>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="size-4 text-[var(--accent)]" /> AI Usage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-xs text-[var(--muted)]">Conversation turns</dt>
              <dd className="text-[var(--foreground)]">{usage.data?.conversation_turns ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-[var(--muted)]">Memories stored</dt>
              <dd className="text-[var(--foreground)]">{usage.data?.memories_stored ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-[var(--muted)]">Tasks pending</dt>
              <dd className="text-[var(--foreground)]">{usage.data?.tasks_pending ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-[var(--muted)]">Model</dt>
              <dd className="text-[var(--foreground)]">{status.data?.model ?? "—"}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ScrollText className="size-4 text-[var(--accent)]" /> Logs
          </CardTitle>
          <CardDescription>Live tail of the backend application log.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="max-h-64 overflow-y-auto rounded-xl border border-[var(--border)] bg-black/40 p-3 font-mono text-[11px] leading-relaxed text-[var(--muted)]">
            {logs.data?.lines.map((line, index) => (
              <div key={index} className={line.includes("ERROR") ? "text-[var(--danger)]" : undefined}>
                {line}
              </div>
            ))}
            {logs.data?.lines.length === 0 && <p>No log entries yet.</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
