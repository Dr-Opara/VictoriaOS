"use client";

import {
  Bot,
  Calendar,
  CheckSquare,
  Cloud,
  Gauge,
  Mail,
  Mic,
  ScrollText,
  Settings,
  Sparkles,
  MessageSquare,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: Gauge },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/voice", label: "Voice", icon: Mic },
  { href: "/email", label: "Email", icon: Mail },
  { href: "/memory", label: "Memory", icon: Sparkles },
  { href: "/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/calendar", label: "Calendar", icon: Calendar },
  { href: "/weather", label: "Weather", icon: Cloud },
  { href: "/usage", label: "AI Usage", icon: Bot },
  { href: "/logs", label: "Logs", icon: ScrollText },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-white/5 bg-black/40 px-3 py-6 md:flex">
      <div className="mb-8 flex items-center gap-2 px-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-sm font-semibold text-black">
          V
        </div>
        <div>
          <p className="text-sm font-semibold leading-none text-neutral-100">Victoria</p>
          <p className="text-xs text-neutral-500">Executive OS</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-white/10 text-white"
                  : "text-neutral-400 hover:bg-white/5 hover:text-neutral-100",
              )}
            >
              <Icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2 text-xs text-neutral-500">
        Dr. Opara &middot; Primary user
      </div>
    </aside>
  );
}
