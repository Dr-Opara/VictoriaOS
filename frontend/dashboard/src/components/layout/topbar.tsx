"use client";

import { useQuery } from "@tanstack/react-query";
import { Circle } from "lucide-react";

import { api } from "@/lib/api";

export function TopBar() {
  const { data, isError } = useQuery({
    queryKey: ["system", "status"],
    queryFn: api.system.status,
    refetchInterval: 10_000,
  });

  const online = !isError && data?.status === "online";

  return (
    <header className="glass sticky top-0 z-10 flex h-14 shrink-0 items-center justify-between px-4 md:px-6">
      <div className="flex items-center gap-2 md:hidden">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--accent)] text-xs font-semibold text-[#03181b]">
          V
        </div>
        <span className="text-sm font-medium text-[var(--foreground)]">Victoria</span>
      </div>

      <div className="hidden md:block" />

      <div className="flex items-center gap-4 text-xs text-[var(--muted)]">
        {data && (
          <span className="hidden sm:inline">
            {data.model} &middot; {data.environment}
          </span>
        )}
        <span className="flex items-center gap-1.5">
          <Circle
            className={
              online
                ? "size-2 fill-[var(--success)] text-[var(--success)]"
                : "size-2 fill-[var(--danger)] text-[var(--danger)]"
            }
          />
          {online ? "Online" : "Offline"}
        </span>
      </div>
    </header>
  );
}
