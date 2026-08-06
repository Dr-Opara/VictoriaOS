"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, Inbox, MailOpen, Reply, Search, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, LoadingState, SkeletonText } from "@/components/ui/state";
import { Input } from "@/components/ui/input";
import { MarkdownMessage } from "@/components/ui/markdown";
import { useToast } from "@/components/ui/toast";
import { api, type EmailMessage } from "@/lib/api";
import { cn } from "@/lib/utils";

function messageKey(message: EmailMessage, index: number): string {
  return `${message.sender}-${message.subject}-${message.date}-${index}`;
}

function isPriority(message: EmailMessage): boolean {
  const text = `${message.sender} ${message.subject} ${message.preview}`.toLowerCase();
  return /\b(urgent|important|asap|payment|invoice|bank|security|deadline|reply|action required)\b/.test(
    text,
  );
}

function filterMessages(messages: EmailMessage[], query: string): EmailMessage[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return messages;

  return messages.filter((message) =>
    `${message.sender} ${message.subject} ${message.date} ${message.preview}`
      .toLowerCase()
      .includes(normalized),
  );
}

export default function EmailPage() {
  const [query, setQuery] = useState("");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const { toast } = useToast();

  const email = useQuery({
    queryKey: ["email", "unread", 30],
    queryFn: () => api.email.unread(30),
    refetchInterval: 30_000,
  });

  const summary = useMutation({
    mutationFn: () => api.email.summarizeUnread(),
    onError: (error) => {
      toast({
        title: "Summary unavailable",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const messages = useMemo(() => email.data?.messages ?? [], [email.data?.messages]);
  const filteredMessages = useMemo(() => filterMessages(messages, query), [messages, query]);
  const priorityMessages = useMemo(() => messages.filter(isPriority), [messages]);
  const activeKey = selectedKey ?? (filteredMessages[0] ? messageKey(filteredMessages[0], 0) : null);
  const selected = filteredMessages.find((message, index) => messageKey(message, index) === activeKey);

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 md:px-8">
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--foreground)]">Yahoo Mail</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Inbox view for unread Yahoo Mail exposed by the v0.2 backend.
          </p>
        </div>
        {email.data && (
          <Badge variant={email.data.configured ? "success" : "warning"}>
            {email.data.configured ? "Connected" : "Not configured"}
          </Badge>
        )}
      </div>

      {email.isLoading && <LoadingState label="Loading Yahoo Mail..." />}
      {email.isError && (
        <ErrorState
          title="Yahoo Mail unavailable"
          description="Victoria could not reach the backend email endpoint."
          action={
            <Button size="sm" variant="outline" onClick={() => email.refetch()}>
              Retry
            </Button>
          }
        />
      )}

      {email.data && !email.data.configured && (
        <Card>
          <CardContent className="p-5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 size-5 text-[var(--warning)]" />
              <div>
                <p className="text-sm font-medium text-[var(--foreground)]">Yahoo Mail is not configured</p>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  The backend returned a disconnected status, so no inbox data is shown.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {email.data?.configured && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[340px_1fr]">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Inbox</CardTitle>
                <CardDescription>{messages.length} unread message(s)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="relative mb-3">
                  <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--muted)]" />
                  <Input
                    placeholder="Search loaded unread mail..."
                    value={query}
                    onChange={(event) => {
                      setQuery(event.target.value);
                      setSelectedKey(null);
                    }}
                    className="pl-9"
                    aria-label="Search loaded unread Yahoo Mail"
                  />
                </div>

                {messages.length === 0 && (
                  <EmptyState
                    icon={Inbox}
                    title="Inbox zero"
                    description="The backend did not return unread Yahoo Mail."
                  />
                )}
                {messages.length > 0 && filteredMessages.length === 0 && (
                  <p className="py-8 text-center text-sm text-[var(--muted)]">
                    No loaded unread messages match that search.
                  </p>
                )}

                <div className="space-y-2">
                  {filteredMessages.map((message, index) => {
                    const key = messageKey(message, index);
                    const active = key === selectedKey;
                    return (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setSelectedKey(key)}
                        className={cn(
                          "w-full rounded-lg border p-3 text-left transition-colors",
                          active
                            ? "border-[var(--accent)] bg-[var(--accent)]/10"
                            : "border-[var(--border)] bg-white/[0.025] hover:border-[var(--accent)]/50",
                        )}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <p className="line-clamp-1 text-sm font-medium text-[var(--foreground)]">
                            {message.subject || "(no subject)"}
                          </p>
                          {isPriority(message) && <Badge variant="warning">Priority</Badge>}
                        </div>
                        <p className="mt-1 line-clamp-1 text-xs text-[var(--muted)]">
                          {message.sender}
                        </p>
                        <p className="mt-1 line-clamp-2 text-xs text-[var(--muted)]">
                          {message.preview}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Priority Messages</CardTitle>
                <CardDescription>Signals derived from loaded unread mail.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {priorityMessages.length === 0 && (
                  <p className="text-sm text-[var(--muted)]">No priority signals found.</p>
                )}
                {priorityMessages.slice(0, 5).map((message, index) => (
                  <div key={messageKey(message, index)} className="rounded-lg bg-white/[0.025] p-3">
                    <p className="line-clamp-1 text-sm font-medium text-[var(--foreground)]">
                      {message.subject}
                    </p>
                    <p className="mt-1 line-clamp-2 text-xs text-[var(--muted)]">
                      {message.sender}: {message.preview}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader className="flex-row items-start justify-between space-y-0">
                <div>
                  <CardTitle>Read Message</CardTitle>
                  <CardDescription>
                    Full message bodies are not exposed by the v0.2 email endpoint.
                  </CardDescription>
                </div>
                <MailOpen className="size-5 text-[var(--accent)]" />
              </CardHeader>
              <CardContent>
                {!selected && (
                  <EmptyState
                    icon={MailOpen}
                    title="No message selected"
                    description="Select an unread message from the inbox list."
                  />
                )}
                {selected && (
                  <div className="space-y-4">
                    <div>
                      <h2 className="text-lg font-semibold text-[var(--foreground)]">
                        {selected.subject || "(no subject)"}
                      </h2>
                      <p className="mt-1 text-sm text-[var(--muted)]">
                        {selected.sender} - {selected.date}
                      </p>
                    </div>
                    <div className="rounded-lg border border-[var(--border)] bg-white/[0.025] p-4">
                      <p className="text-sm leading-relaxed text-[var(--foreground)]/90">
                        {selected.preview || "No preview was returned for this message."}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button type="button" variant="outline" disabled>
                        <MailOpen className="size-4" /> Full body unavailable
                      </Button>
                      <Button type="button" variant="outline" disabled>
                        <Reply className="size-4" /> Draft reply unavailable
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex-row items-start justify-between space-y-0">
                <div>
                  <CardTitle>AI Summary</CardTitle>
                  <CardDescription>Generated through Victoria&apos;s existing assistant API.</CardDescription>
                </div>
                <Sparkles className="size-5 text-[var(--gold)]" />
              </CardHeader>
              <CardContent>
                <Button
                  type="button"
                  onClick={() => summary.mutate()}
                  disabled={summary.isPending || messages.length === 0}
                >
                  <Sparkles className="size-4" />
                  {summary.isPending ? "Summarizing" : "Summarize unread mail"}
                </Button>
                {summary.isPending && <SkeletonText lines={5} />}
                {summary.data && (
                  <div className="mt-4 rounded-lg border border-[var(--border)] bg-white/[0.025] p-4">
                    <MarkdownMessage content={summary.data.response} />
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
