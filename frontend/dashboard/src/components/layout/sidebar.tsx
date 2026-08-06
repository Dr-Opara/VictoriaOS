"use client";

import {
  Bot,
  CheckSquare,
  Home,
  Mail,
  Settings,
  Sparkles,
  Waves,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/assistant", label: "Assistant", icon: Bot },
  { href: "/memory", label: "Memory", icon: Sparkles },
  { href: "/knowledge", label: "Knowledge", icon: Waves },
  { href: "/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/email", label: "Email", icon: Mail },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="glass hidden w-64 shrink-0 flex-col px-3 py-6 md:flex">
      <div className="mb-8 flex items-center gap-2.5 px-2">
        <div className="glow-cyan flex h-9 w-9 items-center justify-center rounded-xl bg-[radial-gradient(circle_at_35%_30%,var(--accent-strong),var(--accent-dim))] text-sm font-semibold text-[#03181b]">
          V
        </div>
        <div>
          <p className="text-sm font-semibold leading-none text-[var(--foreground)]">Victoria</p>
          <p className="text-[11px] text-[var(--muted)]">Executive OS</p>
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
                "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                  : "text-[var(--muted)] hover:bg-white/[0.04] hover:text-[var(--foreground)]",
              )}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-[var(--accent)] shadow-[0_0_10px_var(--accent)]" />
              )}
              <Icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="glass rounded-xl px-3 py-2.5 text-xs text-[var(--muted)]">
        Dr. Opara &middot; Primary user
      </div>
    </aside>
  );
}

export { NAV_ITEMS };
