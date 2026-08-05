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
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-white/5 bg-black/30 px-4 md:px-6">
      <div className="flex items-center gap-2 md:hidden">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-white text-xs font-semibold text-black">
          V
        </div>
        <span className="text-sm font-medium text-neutral-100">Victoria</span>
      </div>

      <div className="hidden md:block" />

      <div className="flex items-center gap-4 text-xs text-neutral-400">
        {data && (
          <span className="hidden sm:inline">
            {data.model} &middot; {data.environment}
          </span>
        )}
        <span className="flex items-center gap-1.5">
          <Circle
            className={online ? "size-2 fill-emerald-400 text-emerald-400" : "size-2 fill-red-500 text-red-500"}
          />
          {online ? "Online" : "Offline"}
        </span>
      </div>
    </header>
  );
}
