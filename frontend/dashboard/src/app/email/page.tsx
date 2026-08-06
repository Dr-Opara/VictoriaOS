"use client";

import { useQuery } from "@tanstack/react-query";
import { Mail } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function EmailPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["email", "unread"],
    queryFn: api.email.unread,
    refetchInterval: 30_000,
  });

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--foreground)]">Email</h1>
          <p className="text-sm text-[var(--muted)]">Yahoo Mail — unread messages</p>
        </div>
        {data && (
          <Badge variant={data.configured ? "success" : "warning"}>
            {data.configured ? "Connected" : "Not configured"}
          </Badge>
        )}
      </div>

      {isLoading && <p className="text-sm text-[var(--muted)]">Loading…</p>}
      {isError && <p className="text-sm text-[var(--danger)]">Could not reach the backend.</p>}
      {data && !data.configured && (
        <p className="text-sm text-[var(--muted)]">
          Set <code>YAHOO_EMAIL</code> and <code>YAHOO_APP_PASSWORD</code> in the backend
          environment to connect Yahoo Mail.
        </p>
      )}
      {data?.error && <p className="text-sm text-[var(--danger)]">{data.error}</p>}

      <div className="space-y-3">
        {data?.messages.map((message, index) => (
          <Card key={`${message.sender}-${index}`}>
            <CardHeader className="flex-row items-start justify-between space-y-0">
              <div>
                <CardTitle>{message.subject}</CardTitle>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  {message.sender} &middot; {message.date}
                </p>
              </div>
              <Mail className="size-4 shrink-0 text-[var(--accent)]" />
            </CardHeader>
            <CardContent>
              <p className="text-sm text-[var(--muted)]">{message.preview}</p>
            </CardContent>
          </Card>
        ))}
        {data?.configured && data.messages.length === 0 && (
          <p className="text-sm text-[var(--muted)]">No unread messages. Inbox zero, Dr. Opara.</p>
        )}
      </div>
    </div>
  );
}
