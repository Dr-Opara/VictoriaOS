"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Check,
  Clock,
  Columns3,
  List,
  Pencil,
  Plus,
  Save,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import type React from "react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/state";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { api, type TaskItem, type TaskPriority } from "@/lib/api";
import { cn } from "@/lib/utils";

type ViewMode = "list" | "board";

const PRIORITY_VARIANT: Record<NonNullable<TaskPriority>, "destructive" | "warning" | "outline"> = {
  high: "destructive",
  medium: "warning",
  low: "outline",
};

function formatDueDate(value: string | null): string {
  if (!value) return "Not set";
  return new Date(value).toLocaleDateString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function sortTasks(tasks: TaskItem[]): TaskItem[] {
  const priorityScore = { high: 0, medium: 1, low: 2 };
  return [...tasks].sort((a, b) => {
    if (a.status !== b.status) return a.status === "pending" ? -1 : 1;
    const aScore = a.priority ? priorityScore[a.priority] : 3;
    const bScore = b.priority ? priorityScore[b.priority] : 3;
    if (aScore !== bScore) return aScore - bScore;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
}

interface TaskCardProps {
  task: TaskItem;
  editing: boolean;
  editTitle: string;
  editDescription: string;
  onEditTitle: (value: string) => void;
  onEditDescription: (value: string) => void;
  onStartEdit: (task: TaskItem) => void;
  onCancelEdit: () => void;
  onSaveEdit: () => void;
  onComplete: (id: number) => void;
  onDelete: (id: number) => void;
  busy: boolean;
}

function TaskCard({
  task,
  editing,
  editTitle,
  editDescription,
  onEditTitle,
  onEditDescription,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onComplete,
  onDelete,
  busy,
}: TaskCardProps) {
  if (editing) {
    return (
      <div className="rounded-lg border border-[var(--accent)]/50 bg-[var(--accent)]/5 p-4">
        <div className="space-y-3">
          <Input
            value={editTitle}
            onChange={(event) => onEditTitle(event.target.value)}
            aria-label="Edit task title"
          />
          <Textarea
            value={editDescription}
            onChange={(event) => onEditDescription(event.target.value)}
            aria-label="Edit task description"
          />
          <p className="text-xs text-[var(--muted)]">
            Save replacement uses the v0.2 create/delete task API because task patching is unavailable.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button type="button" size="sm" onClick={onSaveEdit} disabled={!editTitle.trim() || busy}>
              <Save className="size-4" /> Save replacement
            </Button>
            <Button type="button" size="sm" variant="outline" onClick={onCancelEdit}>
              <X className="size-4" /> Cancel
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "rounded-lg border border-[var(--border)] bg-white/[0.025] p-4",
        task.status === "completed" && "opacity-70",
      )}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Badge variant={task.status === "completed" ? "success" : "secondary"}>
              {task.status}
            </Badge>
            {task.priority ? (
              <Badge variant={PRIORITY_VARIANT[task.priority]}>{task.priority}</Badge>
            ) : (
              <Badge variant="outline">No priority</Badge>
            )}
          </div>
          <p
            className={cn(
              "break-words text-sm font-medium text-[var(--foreground)]",
              task.status === "completed" && "line-through",
            )}
          >
            {task.title}
          </p>
          {task.description && (
            <p className="mt-1 break-words text-sm text-[var(--muted)]">{task.description}</p>
          )}
          <p className="mt-2 flex items-center gap-1.5 text-xs text-[var(--muted)]">
            <Clock className="size-3.5" /> Due {formatDueDate(task.due_at)}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => onStartEdit(task)}
            aria-label={`Edit ${task.title}`}
          >
            <Pencil className="size-4" />
          </Button>
          {task.status === "pending" && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => onComplete(task.id)}
              disabled={busy}
              aria-label={`Complete ${task.title}`}
            >
              <Check className="size-4" />
            </Button>
          )}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => onDelete(task.id)}
            disabled={busy}
            aria-label={`Delete ${task.title}`}
          >
            <Trash2 className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function TasksPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [editingTask, setEditingTask] = useState<TaskItem | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const tasks = useQuery({
    queryKey: ["tasks"],
    queryFn: () => api.tasks.list(),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["tasks"] });

  const create = useMutation({
    mutationFn: () => api.tasks.create(title.trim(), description.trim()),
    onSuccess: () => {
      setTitle("");
      setDescription("");
      invalidate();
      toast({ title: "Task created", variant: "success" });
    },
    onError: (error) => {
      toast({
        title: "Could not create task",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const replace = useMutation({
    mutationFn: () => {
      if (!editingTask) throw new Error("No task selected.");
      return api.tasks.replace(editingTask, editTitle.trim(), editDescription.trim());
    },
    onSuccess: () => {
      setEditingTask(null);
      setEditTitle("");
      setEditDescription("");
      invalidate();
      toast({ title: "Task replaced", variant: "success" });
    },
    onError: (error) => {
      toast({
        title: "Could not replace task",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const complete = useMutation({
    mutationFn: (id: number) => api.tasks.complete(id),
    onSuccess: () => {
      invalidate();
      toast({ title: "Task completed", variant: "success" });
    },
    onError: (error) => {
      toast({
        title: "Could not complete task",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.tasks.remove(id),
    onSuccess: () => {
      invalidate();
      toast({ title: "Task deleted", variant: "success" });
    },
    onError: (error) => {
      toast({
        title: "Could not delete task",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const prioritize = useMutation({
    mutationFn: () => api.tasks.prioritize(),
    onSuccess: (data) => {
      invalidate();
      toast({
        title: "Tasks prioritized",
        description: `Victoria ranked ${data.plans.length} pending task(s).`,
        variant: "success",
      });
    },
    onError: (error) => {
      toast({
        title: "Prioritization failed",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const items = useMemo(() => sortTasks(tasks.data?.tasks ?? []), [tasks.data]);
  const pending = items.filter((task) => task.status === "pending");
  const completed = items.filter((task) => task.status === "completed");
  const busy =
    create.isPending ||
    replace.isPending ||
    complete.isPending ||
    remove.isPending ||
    prioritize.isPending;

  const startEdit = (task: TaskItem) => {
    setEditingTask(task);
    setEditTitle(task.title);
    setEditDescription(task.description);
  };

  const submitCreate = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!title.trim() || create.isPending) return;
    create.mutate();
  };

  const renderTask = (task: TaskItem) => (
    <TaskCard
      key={task.id}
      task={task}
      editing={editingTask?.id === task.id}
      editTitle={editTitle}
      editDescription={editDescription}
      onEditTitle={setEditTitle}
      onEditDescription={setEditDescription}
      onStartEdit={startEdit}
      onCancelEdit={() => setEditingTask(null)}
      onSaveEdit={() => replace.mutate()}
      onComplete={(id) => complete.mutate(id)}
      onDelete={(id) => remove.mutate(id)}
      busy={busy}
    />
  );

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 md:px-8">
      <div className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--foreground)]">Tasks</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Create, complete, delete, prioritize, and replace tasks through the existing backend API.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="flex rounded-lg border border-[var(--border)] p-1">
            <Button
              type="button"
              size="sm"
              variant={viewMode === "list" ? "default" : "ghost"}
              onClick={() => setViewMode("list")}
            >
              <List className="size-4" /> List
            </Button>
            <Button
              type="button"
              size="sm"
              variant={viewMode === "board" ? "default" : "ghost"}
              onClick={() => setViewMode("board")}
            >
              <Columns3 className="size-4" /> Board
            </Button>
          </div>
          <Button
            type="button"
            variant="secondary"
            onClick={() => prioritize.mutate()}
            disabled={prioritize.isPending || pending.length === 0}
          >
            <Sparkles className="size-4" />
            {prioritize.isPending ? "Prioritizing" : "Prioritize with AI"}
          </Button>
        </div>
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Create Task</CardTitle>
          <CardDescription>Priority is set by AI prioritization. Due dates are read-only in v0.2.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid grid-cols-1 gap-3 lg:grid-cols-[1fr_1.2fr_auto]" onSubmit={submitCreate}>
            <Input
              placeholder="Task title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              aria-label="Task title"
            />
            <Input
              placeholder="Description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              aria-label="Task description"
            />
            <Button type="submit" disabled={!title.trim() || create.isPending}>
              <Plus className="size-4" /> {create.isPending ? "Adding" : "Add"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {tasks.isLoading && <LoadingState label="Loading tasks..." />}
      {tasks.isError && (
        <ErrorState
          title="Tasks unavailable"
          description="Victoria could not read tasks from the backend."
          action={
            <Button size="sm" variant="outline" onClick={() => tasks.refetch()}>
              Retry
            </Button>
          }
        />
      )}
      {tasks.isSuccess && items.length === 0 && (
        <Card>
          <CardContent>
            <EmptyState
              icon={Check}
              title="No tasks yet"
              description="Create a task above, or ask Victoria to track work for you."
            />
          </CardContent>
        </Card>
      )}

      {tasks.isSuccess && items.length > 0 && viewMode === "list" && (
        <div className="space-y-3">{items.map(renderTask)}</div>
      )}

      {tasks.isSuccess && items.length > 0 && viewMode === "board" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Pending</CardTitle>
              <CardDescription>{pending.length} task(s)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {pending.length === 0 && (
                <p className="text-sm text-[var(--muted)]">No pending tasks.</p>
              )}
              {pending.map(renderTask)}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Completed</CardTitle>
              <CardDescription>{completed.length} task(s)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {completed.length === 0 && (
                <p className="text-sm text-[var(--muted)]">No completed tasks.</p>
              )}
              {completed.map(renderTask)}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
