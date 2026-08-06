import { AlertTriangle, type LucideIcon, Loader2 } from "lucide-react";
import type React from "react";

import { cn } from "@/lib/utils";

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-[var(--muted)]">
      <Loader2 className="size-5 animate-spin text-[var(--accent)] motion-reduce:animate-none" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description = "Please try again in a moment.",
  action,
}: {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
      <AlertTriangle className="size-6 text-[var(--danger)]" />
      <p className="text-sm font-medium text-[var(--foreground)]">{title}</p>
      <p className="max-w-sm text-xs text-[var(--muted)]">{description}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <Icon className="size-8 text-[var(--muted)]" />
      <div>
        <p className="text-sm font-medium text-[var(--foreground)]">{title}</p>
        <p className="mt-1 max-w-sm text-sm text-[var(--muted)]">{description}</p>
      </div>
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-white/[0.06] motion-reduce:animate-none",
        className,
      )}
    />
  );
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2 py-2" aria-hidden="true">
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className={cn("h-3", index === lines - 1 ? "w-2/3" : "w-full")}
        />
      ))}
    </div>
  );
}
