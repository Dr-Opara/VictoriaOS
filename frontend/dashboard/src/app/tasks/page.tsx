"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Trash2 } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function TasksPage() {
  const [title, setTitle] = useState("");
  const queryClient = useQueryClient();

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

  const items = tasks.data?.tasks ?? [];
  const pending = items.filter((task) => task.status === "pending");
  const completed = items.filter((task) => task.status === "completed");

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-8">
      <h1 className="text-xl font-semibold text-neutral-50">Tasks</h1>
      <p className="mb-6 text-sm text-neutral-500">What Victoria is tracking for you.</p>

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
              <div>
                <p className="text-sm font-medium text-neutral-100">{task.title}</p>
                {task.description && (
                  <p className="text-xs text-neutral-500">{task.description}</p>
                )}
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
          <p className="text-sm text-neutral-500">No pending tasks.</p>
        )}
      </div>

      {completed.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-600">
            Completed
          </h2>
          <div className="space-y-2">
            {completed.map((task) => (
              <Card key={task.id} className="opacity-60">
                <CardContent className="flex items-center justify-between pt-4">
                  <p className={cn("text-sm line-through text-neutral-400")}>{task.title}</p>
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
