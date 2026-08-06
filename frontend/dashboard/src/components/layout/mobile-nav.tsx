"use client";

import { Bot, CheckSquare, Home, Settings, Sparkles } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const MOBILE_ITEMS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/assistant", label: "Assistant", icon: Bot },
  { href: "/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/knowledge", label: "Knowledge", icon: Sparkles },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="glass-strong fixed inset-x-0 bottom-0 z-20 flex items-center justify-around py-2 md:hidden">
      {MOBILE_ITEMS.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center gap-0.5 px-3 py-1 text-[10px] font-medium",
              isActive ? "text-[var(--accent)]" : "text-[var(--muted)]",
            )}
          >
            <Icon className="size-5" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
