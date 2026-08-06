"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  CheckSquare,
  Cpu,
  Database,
  FileText,
  HardDrive,
  Mail,
  MessageSquare,
  Radio,
  Server,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { AICore, type AICoreState } from "@/components/ai-core/ai-core";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, Skeleton, SkeletonText } from "@/components/ui/state";
import { api, type EmailMessage, type TaskItem } from "@/lib/api";
import { loadStoredChat, type StoredChatMessage } from "@/lib/local-chat";

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning, Dr. Opara.";
  if (hour < 18) return "Good afternoon, Dr. Opara.";
  return "Good evening, Dr. Opara.";
}

function formatUptime(seconds?: number): string {
  if (seconds === undefined) return "-";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function isPriorityMessage(message: EmailMessage): boolean {
  const text = `${message.sender} ${message.subject} ${message.preview}`.toLowerCase();
  return /\b(urgent|important|asap|invoice|payment|bank|security|action required|deadline|reply)\b/.test(
    text,
  );
}

function sortedPendingTasks(tasks: TaskItem[]): TaskItem[] {
  const priorityScore = { high: 0, medium: 1, low: 2 };
  return tasks
    .filter((task) => task.status === "pending")
    .sort((a, b) => {
      const aScore = a.priority ? priorityScore[a.priority] : 3;
      const bScore = b.priority ? priorityScore[b.priority] : 3;
      return aScore - bScore;
    });
}

function StatusLine({
  icon: Icon,
  label,
  value,
  tone = "neutral",
}: {
  icon: typeof CheckCircle2;
  label: string;
  value: string;
  tone?: "good" | "warn" | "bad" | "neutral";
}) {
  const toneClass =
    tone === "good"
      ? "text-[var(--success)]"
      : tone === "warn"
        ? "text-[var(--warning)]"
        : tone === "bad"
          ? "text-[var(--danger)]"
          : "text-[var(--muted)]";

  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-[var(--border)] bg-white/[0.025] px-3 py-2.5">
      <div className="flex min-w-0 items-center gap-2">
        <Icon className={`size-4 shrink-0 ${toneClass}`} />
        <span className="truncate text-sm text-[var(--foreground)]">{label}</span>
      </div>
      <span className={`shrink-0 text-xs ${toneClass}`}>{value}</span>
    </div>
  );
}

export default function HomePage() {
  const [recentChat, setRecentChat] = useState<StoredChatMessage[]>([]);

  useEffect(() => {
    queueMicrotask(() => setRecentChat(loadStoredChat().slice(-4)));
  }, []);

  const status = useQuery({
    queryKey: ["system", "status"],
    queryFn: api.system.status,
    refetchInterval: 10_000,
  });

  const health = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 10_000,
  });

  const usage = useQuery({
    queryKey: ["system", "usage"],
    queryFn: api.system.usage,
    refetchInterval: 15_000,
  });

  const email = useQuery({
    queryKey: ["email", "unread", 12],
    queryFn: () => api.email.unread(12),
    refetchInterval: 30_000,
  });

  const tasks = useQuery({
    queryKey: ["tasks"],
    queryFn: () => api.tasks.list(),
    refetchInterval: 20_000,
  });

  const memories = useQuery({
    queryKey: ["memory", "recent"],
    queryFn: () => api.memory.list(undefined, 6),
    refetchInterval: 30_000,
  });

  const documents = useQuery({
    queryKey: ["knowledge", "documents"],
    queryFn: api.knowledge.list,
    refetchInterval: 45_000,
  });

  const voice = useQuery({
    queryKey: ["voice", "connect"],
    queryFn: api.voice.connect,
    refetchInterval: 30_000,
  });

  const briefing = useQuery({
    queryKey: ["briefing"],
    queryFn: api.briefing.get,
    staleTime: 5 * 60_000,
  });

  const pendingTasks = useMemo(() => sortedPendingTasks(tasks.data?.tasks ?? []), [tasks.data]);
  const priorityMail = useMemo(
    () => (email.data?.messages ?? []).filter(isPriorityMessage).slice(0, 3),
    [email.data],
  );

  const coreState: AICoreState =
    status.isError || Boolean(status.data && status.data.status !== "online")
      ? "offline"
      : briefing.isError
        ? "error"
        : briefing.isFetching
          ? "thinking"
          : "idle";

  const stats = [
    {
      label: "Unread Yahoo Mail",
      value: email.isLoading ? "-" : email.data?.configured ? email.data.messages.length : "Off",
      icon: Mail,
    },
    {
      label: "Pending tasks",
      value: usage.data?.tasks_pending ?? "-",
      icon: CheckSquare,
    },
    {
      label: "Memories",
      value: usage.data?.memories_stored ?? "-",
      icon: Sparkles,
    },
    {
      label: "Documents",
      value: documents.data?.documents.length ?? "-",
      icon: FileText,
    },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 md:px-8">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-semibold text-[var(--foreground)] text-glow">
            {greeting()}
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Victoria is tracking the v0.2 operating surface.
          </p>
        </motion.div>
        <AICore
          state={coreState}
          size={96}
          label={
            coreState === "offline"
              ? "Backend offline"
              : coreState === "error"
                ? "Briefing error"
                : coreState === "thinking"
                  ? "Briefing"
                  : "Systems ready"
          }
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04 }}
          >
            <Card>
              <CardContent className="flex items-center justify-between p-5">
                <div>
                  <p className="text-xs text-[var(--muted)]">{stat.label}</p>
                  <p className="mt-1 text-2xl font-semibold text-[var(--foreground)]">
                    {stat.value}
                  </p>
                </div>
                <stat.icon className="size-5 text-[var(--accent)]" />
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 xl:grid-cols-[1.35fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Executive Briefing</CardTitle>
            <CardDescription>Generated by the backend briefing service.</CardDescription>
          </CardHeader>
          <CardContent>
            {briefing.isLoading && <SkeletonText lines={6} />}
            {briefing.isError && (
              <ErrorState
                title="Briefing unavailable"
                description="Victoria could not generate a backend briefing right now."
                action={
                  <Button size="sm" variant="outline" onClick={() => briefing.refetch()}>
                    Retry
                  </Button>
                }
              />
            )}
            {briefing.data && (
              <p className="whitespace-pre-line text-sm leading-relaxed text-[var(--foreground)]/90">
                {briefing.data.briefing}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Service Health</CardTitle>
            <CardDescription>Live checks from existing VictoriaOS APIs.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <StatusLine
              icon={Server}
              label="Mini PC API"
              value={health.isLoading ? "Checking" : health.isSuccess ? "Healthy" : "Offline"}
              tone={health.isSuccess ? "good" : health.isError ? "bad" : "neutral"}
            />
            <StatusLine
              icon={Database}
              label="Database"
              value={usage.isLoading ? "Checking" : usage.isSuccess ? "Reachable" : "Error"}
              tone={usage.isSuccess ? "good" : usage.isError ? "bad" : "neutral"}
            />
            <StatusLine
              icon={Bot}
              label="OpenAI"
              value={briefing.isLoading ? "Checking" : briefing.isSuccess ? "Responding" : "Error"}
              tone={briefing.isSuccess ? "good" : briefing.isError ? "bad" : "neutral"}
            />
            <StatusLine
              icon={Radio}
              label="Raspberry Pi voice link"
              value={voice.isLoading ? "Checking" : voice.isSuccess ? "API ready" : "No signal"}
              tone={voice.isSuccess ? "good" : voice.isError ? "warn" : "neutral"}
            />
            <StatusLine
              icon={HardDrive}
              label="Knowledge store"
              value={
                documents.isLoading
                  ? "Checking"
                  : documents.isSuccess
                    ? `${documents.data.documents.length} docs`
                    : "Error"
              }
              tone={documents.isSuccess ? "good" : documents.isError ? "bad" : "neutral"}
            />
          </CardContent>
        </Card>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Yahoo Mail Summary</CardTitle>
              <CardDescription>Unread messages from Yahoo Mail.</CardDescription>
            </div>
            {email.data && (
              <Badge variant={email.data.configured ? "success" : "warning"}>
                {email.data.configured ? "Connected" : "Not configured"}
              </Badge>
            )}
          </CardHeader>
          <CardContent className="space-y-3">
            {email.isLoading && <Skeleton className="h-20" />}
            {email.isError && (
              <p className="text-sm text-[var(--danger)]">Yahoo Mail status could not be loaded.</p>
            )}
            {email.data && !email.data.configured && (
              <p className="text-sm text-[var(--muted)]">
                Yahoo Mail credentials are not configured in the backend.
              </p>
            )}
            {email.data?.configured && email.data.messages.length === 0 && (
              <p className="text-sm text-[var(--muted)]">No unread Yahoo Mail messages.</p>
            )}
            {priorityMail.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-[var(--warning)]">Priority signals</p>
                {priorityMail.map((message, index) => (
                  <div key={`${message.sender}-${index}`} className="rounded-lg bg-white/[0.025] p-3">
                    <p className="line-clamp-1 text-sm font-medium text-[var(--foreground)]">
                      {message.subject}
                    </p>
                    <p className="mt-1 line-clamp-2 text-xs text-[var(--muted)]">
                      {message.sender}: {message.preview}
                    </p>
                  </div>
                ))}
              </div>
            )}
            <Button asChild variant="outline" size="sm">
              <Link href="/email">Open Yahoo Mail</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Task Summary</CardTitle>
            <CardDescription>Pending work sorted by current priority.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {tasks.isLoading && <SkeletonText lines={4} />}
            {tasks.isError && (
              <p className="text-sm text-[var(--danger)]">Tasks could not be loaded.</p>
            )}
            {tasks.isSuccess && pendingTasks.length === 0 && (
              <p className="text-sm text-[var(--muted)]">No pending tasks.</p>
            )}
            {pendingTasks.slice(0, 4).map((task) => (
              <div key={task.id} className="rounded-lg bg-white/[0.025] p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="line-clamp-1 text-sm font-medium text-[var(--foreground)]">
                    {task.title}
                  </p>
                  {task.priority && <Badge variant="outline">{task.priority}</Badge>}
                </div>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  Due {task.due_at ? new Date(task.due_at).toLocaleDateString() : "not set"}
                </p>
              </div>
            ))}
            <Button asChild variant="outline" size="sm">
              <Link href="/tasks">Open Tasks</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Memory Summary</CardTitle>
            <CardDescription>Recent facts Victoria can recall.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {memories.isLoading && <SkeletonText lines={4} />}
            {memories.isError && (
              <p className="text-sm text-[var(--danger)]">Memory could not be loaded.</p>
            )}
            {memories.isSuccess && memories.data.memories.length === 0 && (
              <p className="text-sm text-[var(--muted)]">No memories stored yet.</p>
            )}
            {memories.data?.memories.slice(0, 4).map((memory) => (
              <div key={`${memory.key}-${memory.created_at}`} className="rounded-lg bg-white/[0.025] p-3">
                <p className="line-clamp-1 text-sm font-medium text-[var(--foreground)]">
                  {memory.key}
                </p>
                <p className="mt-1 line-clamp-2 text-xs text-[var(--muted)]">{memory.value}</p>
              </div>
            ))}
            <Button asChild variant="outline" size="sm">
              <Link href="/memory">Open Memory</Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Recent Conversation</CardTitle>
            <CardDescription>Latest local Assistant messages on this dashboard.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {recentChat.length === 0 && (
              <p className="text-sm text-[var(--muted)]">
                No local Assistant conversation has been saved yet.
              </p>
            )}
            {recentChat.map((message) => (
              <div key={message.id} className="rounded-lg bg-white/[0.025] p-3">
                <div className="mb-1 flex items-center gap-2">
                  <MessageSquare className="size-3.5 text-[var(--accent)]" />
                  <span className="text-xs text-[var(--muted)]">
                    {message.role === "user" ? "Dr. Opara" : "Victoria"}
                  </span>
                </div>
                <p className="line-clamp-2 text-sm text-[var(--foreground)]">{message.content}</p>
              </div>
            ))}
            <Button asChild variant="outline" size="sm">
              <Link href="/assistant">Continue Chat</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Runtime Snapshot</CardTitle>
            <CardDescription>Mini PC process, model, and voice configuration.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-[var(--border)] bg-white/[0.025] p-3">
              <Cpu className="mb-2 size-4 text-[var(--accent)]" />
              <p className="text-xs text-[var(--muted)]">Environment</p>
              <p className="mt-1 text-sm text-[var(--foreground)]">
                {status.data?.environment ?? "-"}
              </p>
            </div>
            <div className="rounded-lg border border-[var(--border)] bg-white/[0.025] p-3">
              <Activity className="mb-2 size-4 text-[var(--success)]" />
              <p className="text-xs text-[var(--muted)]">Uptime</p>
              <p className="mt-1 text-sm text-[var(--foreground)]">
                {formatUptime(status.data?.uptime_seconds)}
              </p>
            </div>
            <div className="rounded-lg border border-[var(--border)] bg-white/[0.025] p-3">
              <Bot className="mb-2 size-4 text-[var(--violet)]" />
              <p className="text-xs text-[var(--muted)]">Model</p>
              <p className="mt-1 text-sm text-[var(--foreground)]">{status.data?.model ?? "-"}</p>
            </div>
            <div className="rounded-lg border border-[var(--border)] bg-white/[0.025] p-3">
              {voice.isError ? (
                <AlertTriangle className="mb-2 size-4 text-[var(--warning)]" />
              ) : (
                <Radio className="mb-2 size-4 text-[var(--gold)]" />
              )}
              <p className="text-xs text-[var(--muted)]">Wake word</p>
              <p className="mt-1 text-sm text-[var(--foreground)]">
                {voice.data?.wake_word ?? "Unavailable"}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
