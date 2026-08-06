"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Pin, Plus, Save, Search, Trash2, X } from "lucide-react";
import type React from "react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/state";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { api, type MemoryItem } from "@/lib/api";

function memoryId(memory: MemoryItem): string {
  return `${memory.key}-${memory.created_at}`;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function MemoryPage() {
  const [query, setQuery] = useState("");
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editKey, setEditKey] = useState("");
  const [editValue, setEditValue] = useState("");
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const memories = useQuery({
    queryKey: ["memory", query],
    queryFn: () => api.memory.list(query || undefined, 50),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["memory"] });

  const remember = useMutation({
    mutationFn: () => api.memory.remember(key.trim(), value.trim()),
    onSuccess: () => {
      setKey("");
      setValue("");
      invalidate();
      toast({ title: "Memory created", variant: "success" });
    },
    onError: (error) => {
      toast({
        title: "Could not create memory",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const replace = useMutation({
    mutationFn: () => api.memory.replace(editKey.trim(), editValue.trim()),
    onSuccess: () => {
      setEditingId(null);
      setEditKey("");
      setEditValue("");
      invalidate();
      toast({ title: "Memory updated", variant: "success" });
    },
    onError: (error) => {
      toast({
        title: "Could not update memory",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const forget = useMutation({
    mutationFn: (memoryKey: string) => api.memory.forget(memoryKey),
    onSuccess: (result) => {
      invalidate();
      toast({
        title: "Memory deleted",
        description: `${result.removed} entr${result.removed === 1 ? "y" : "ies"} removed.`,
        variant: "success",
      });
    },
    onError: (error) => {
      toast({
        title: "Could not delete memory",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const startEdit = (memory: MemoryItem) => {
    setEditingId(memoryId(memory));
    setEditKey(memory.key);
    setEditValue(memory.value);
  };

  const submitCreate = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!key.trim() || !value.trim() || remember.isPending) return;
    remember.mutate();
  };

  const visibleMemories = memories.data?.memories ?? [];

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 md:px-8">
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--foreground)]">Memory</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Durable facts Victoria can recall through the backend memory API.
          </p>
        </div>
        <Badge variant="outline">{visibleMemories.length} loaded</Badge>
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Create Memory</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid grid-cols-1 gap-3 md:grid-cols-[220px_1fr_auto]" onSubmit={submitCreate}>
            <Input
              placeholder="Key"
              value={key}
              onChange={(event) => setKey(event.target.value)}
              aria-label="Memory key"
            />
            <Input
              placeholder="Value"
              value={value}
              onChange={(event) => setValue(event.target.value)}
              aria-label="Memory value"
            />
            <Button type="submit" disabled={!key.trim() || !value.trim() || remember.isPending}>
              <Plus className="size-4" /> {remember.isPending ? "Saving" : "Remember"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="mb-4 flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--muted)]" />
          <Input
            placeholder="Search memories..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="pl-9"
            aria-label="Search memories"
          />
        </div>
        {query && (
          <Button type="button" variant="ghost" size="icon" onClick={() => setQuery("")} aria-label="Clear search">
            <X className="size-4" />
          </Button>
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          {memories.isLoading && <LoadingState label="Loading memories..." />}
          {memories.isError && (
            <ErrorState
              title="Memory unavailable"
              description="Victoria could not read memories from the backend."
              action={
                <Button size="sm" variant="outline" onClick={() => memories.refetch()}>
                  Retry
                </Button>
              }
            />
          )}
          {memories.isSuccess && visibleMemories.length === 0 && (
            <EmptyState
              icon={Search}
              title={query ? "No matching memories" : "No memories yet"}
              description={
                query
                  ? "Try a different search term."
                  : "Create the first memory above, or ask Victoria to remember something."
              }
            />
          )}

          <div className="divide-y divide-[var(--border)]">
            {visibleMemories.map((memory) => {
              const id = memoryId(memory);
              const isEditing = editingId === id;

              return (
                <div key={id} className="p-4">
                  {isEditing ? (
                    <div className="space-y-3">
                      <Input
                        value={editKey}
                        onChange={(event) => setEditKey(event.target.value)}
                        aria-label="Edit memory key"
                      />
                      <Textarea
                        value={editValue}
                        onChange={(event) => setEditValue(event.target.value)}
                        aria-label="Edit memory value"
                      />
                      <p className="text-xs text-[var(--muted)]">
                        Saving replaces every memory stored under this key.
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          type="button"
                          size="sm"
                          onClick={() => replace.mutate()}
                          disabled={!editKey.trim() || !editValue.trim() || replace.isPending}
                        >
                          <Save className="size-4" /> Save
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => setEditingId(null)}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="break-words text-sm font-medium text-[var(--foreground)]">
                            {memory.key}
                          </p>
                          <span className="text-xs text-[var(--muted)]">
                            {formatDate(memory.created_at)}
                          </span>
                        </div>
                        <p className="mt-1 break-words text-sm text-[var(--muted)]">{memory.value}</p>
                      </div>
                      <div className="flex shrink-0 items-center gap-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => startEdit(memory)}
                          aria-label={`Edit ${memory.key}`}
                        >
                          <Pencil className="size-4" />
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          disabled
                          title="Pinning is not exposed by the v0.2 memory API."
                          aria-label="Pin unavailable"
                        >
                          <Pin className="size-4" />
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => forget.mutate(memory.key)}
                          disabled={forget.isPending}
                          aria-label={`Delete ${memory.key}`}
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
