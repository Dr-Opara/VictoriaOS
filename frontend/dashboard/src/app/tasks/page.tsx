"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Sparkles, Trash2 } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/state";
import { useToast } from "@/components/ui/toast";
import { type TaskPriority, api } from "@/lib/api";
import { cn } from "@/lib/utils";

const PRIORITY_VARIANT: Record<NonNullable<TaskPriority>, "destructive" | "warning" | "outline"> = {
  high: "destructive",
  medium: "warning",
  low: "outline",
};

export default function TasksPage() {
  const [title, setTitle] = useState("");
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const tasks = useQuery({ queryKey: ["tasks"], queryFn: () => api.tasks.list() });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["tasks"] });

  const create = useMutation({
    mutationFn: () => api.tasks.create(title),
    onSuccess: () => {
      setTitle("");
      invalidate();
    },
  });

  const complete = useMutation({
    mutationFn: (id: number) => api.tasks.complete(id),
    onSuccess: invalidate,
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.tasks.remove(id),
    onSuccess: invalidate,
  });

  const prioritize = useMutation({
    mutationFn: () => api.tasks.prioritize(),
    onSuccess: (data) => {
      toast({
        title: "Tasks prioritized",
        description: `Victoria ranked ${data.plans.length} task(s).`,
        variant: "success",
      });
      invalidate();
    },
    onError: () => {
      toast({ title: "Prioritization failed", description: "Try again shortly.", variant: "error" });
    },
  });

  const items = tasks.data?.tasks ?? [];
  const pending = items.filter((task) => task.status === "pending");
  const completed = items.filter((task) => task.status === "completed");

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--foreground)]">Tasks</h1>
          <p className="text-sm text-[var(--muted)]">What Victoria is tracking for you.</p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => prioritize.mutate()}
          disabled={prioritize.isPending || pending.length === 0}
        >
          <Sparkles className="size-4" /> {prioritize.isPending ? "Thinking…" : "Prioritize with AI"}
        </Button>
      </div>

      <div className="mb-6 flex gap-2">
        <Input
          placeholder="New task…"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && title.trim()) create.mutate();
          }}
        />
        <Button onClick={() => create.mutate()} disabled={!title.trim() || create.isPending}>
          Add
        </Button>
      </div>

      <div className="space-y-2">
        {pending.map((task) => (
          <Card key={task.id}>
            <CardContent className="flex items-center justify-between pt-4">
              <div className="flex items-center gap-3">
                {task.priority && (
                  <Badge variant={PRIORITY_VARIANT[task.priority]}>{task.priority}</Badge>
                )}
                <div>
                  <p className="text-sm font-medium text-[var(--foreground)]">{task.title}</p>
                  {task.description && (
                    <p className="text-xs text-[var(--muted)]">{task.description}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" onClick={() => complete.mutate(task.id)}>
                  <Check className="size-4" />
                </Button>
                <Button variant="ghost" size="icon" onClick={() => remove.mutate(task.id)}>
                  <Trash2 className="size-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {pending.length === 0 && !tasks.isLoading && (
          <EmptyState
            icon={Check}
            title="No pending tasks"
            description="Add a task above, or ask Victoria to create one for you."
          />
        )}
      </div>

      {completed.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--accent)]">
            Completed
          </h2>
          <div className="space-y-2">
            {completed.map((task) => (
              <Card key={task.id} className="opacity-60">
                <CardContent className="flex items-center justify-between pt-4">
                  <p className={cn("text-sm line-through text-[var(--muted)]")}>{task.title}</p>
                  <Badge variant="secondary">Done</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
