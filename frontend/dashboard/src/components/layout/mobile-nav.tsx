"use client";

import { Bot, CheckSquare, Gauge, MessageSquare, Mic } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const MOBILE_ITEMS = [
  { href: "/", label: "Home", icon: Gauge },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/voice", label: "Voice", icon: Mic },
  { href: "/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/usage", label: "Usage", icon: Bot },
] as const;

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 flex items-center justify-around border-t border-white/5 bg-black/80 py-2 backdrop-blur md:hidden">
      {MOBILE_ITEMS.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center gap-0.5 px-3 py-1 text-[10px] font-medium",
              isActive ? "text-white" : "text-neutral-500",
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
