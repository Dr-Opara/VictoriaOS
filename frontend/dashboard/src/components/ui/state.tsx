import { AlertTriangle, type LucideIcon, Loader2 } from "lucide-react";

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-[var(--muted)]">
      <Loader2 className="size-5 animate-spin text-[var(--accent)]" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description = "Please try again in a moment.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
      <AlertTriangle className="size-6 text-[var(--danger)]" />
      <p className="text-sm font-medium text-[var(--foreground)]">{title}</p>
      <p className="max-w-sm text-xs text-[var(--muted)]">{description}</p>
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
