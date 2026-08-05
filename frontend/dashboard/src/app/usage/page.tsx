"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function UsagePage() {
  const usage = useQuery({
    queryKey: ["system", "usage"],
    queryFn: api.system.usage,
    refetchInterval: 10_000,
  });

  const status = useQuery({
    queryKey: ["system", "status"],
    queryFn: api.system.status,
    refetchInterval: 10_000,
  });

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-8">
      <h1 className="text-xl font-semibold text-neutral-50">AI Usage</h1>
      <p className="mb-6 text-sm text-neutral-500">
        Executive assistant activity across the current database.
      </p>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Conversation turns</CardTitle>
            <CardDescription>Total exchanges recorded</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-neutral-50">
              {usage.data?.conversation_turns ?? "—"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Memories stored</CardTitle>
            <CardDescription>Long-term facts remembered</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-neutral-50">
              {usage.data?.memories_stored ?? "—"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Tasks</CardTitle>
            <CardDescription>Pending / total</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-neutral-50">
              {usage.data?.tasks_pending ?? "—"} / {usage.data?.tasks_total ?? "—"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Model</CardTitle>
            <CardDescription>Active GPT model</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-neutral-50">{status.data?.model ?? "—"}</p>
          </CardContent>
        </Card>
      </div>

      <p className="mt-6 text-xs text-neutral-600">
        Per-request token/cost tracking is not yet implemented — it needs the OpenAI usage
        response fields to be captured and persisted per call.
      </p>
    </div>
  );
}
