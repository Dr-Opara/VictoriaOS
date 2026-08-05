"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Bot, CheckSquare, Mail, Sparkles } from "lucide-react";
import Link from "next/link";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function OverviewPage() {
  const status = useQuery({
    queryKey: ["system", "status"],
    queryFn: api.system.status,
    refetchInterval: 10_000,
  });

  const usage = useQuery({
    queryKey: ["system", "usage"],
    queryFn: api.system.usage,
    refetchInterval: 10_000,
  });

  const email = useQuery({
    queryKey: ["email", "unread"],
    queryFn: api.email.unread,
    refetchInterval: 30_000,
  });

  const stats = [
    { label: "Conversation turns", value: usage.data?.conversation_turns ?? "—", icon: Bot },
    { label: "Memories stored", value: usage.data?.memories_stored ?? "—", icon: Sparkles },
    { label: "Pending tasks", value: usage.data?.tasks_pending ?? "—", icon: CheckSquare },
    {
      label: "Unread email",
      value: email.data?.configured ? email.data.messages.length : "—",
      icon: Mail,
    },
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 md:px-8">
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-50">
          Good to see you, Dr. Opara.
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Here is what Victoria is tracking right now.
        </p>
      </motion.div>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card>
              <CardContent className="flex items-center justify-between pt-5">
                <div>
                  <p className="text-xs text-neutral-500">{stat.label}</p>
                  <p className="mt-1 text-2xl font-semibold text-neutral-50">{stat.value}</p>
                </div>
                <stat.icon className="size-5 text-neutral-600" />
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>System status</CardTitle>
            <CardDescription>Live from the VictoriaOS backend</CardDescription>
          </CardHeader>
          <CardContent>
            {status.isError && (
              <p className="text-sm text-red-400">
                Backend is unreachable. Is it running on port 8000?
              </p>
            )}
            {status.data && (
              <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                <div>
                  <dt className="text-xs text-neutral-500">Status</dt>
                  <dd className="text-neutral-100">{status.data.status}</dd>
                </div>
                <div>
                  <dt className="text-xs text-neutral-500">Uptime</dt>
                  <dd className="text-neutral-100">{Math.round(status.data.uptime_seconds)}s</dd>
                </div>
                <div>
                  <dt className="text-xs text-neutral-500">Model</dt>
                  <dd className="text-neutral-100">{status.data.model}</dd>
                </div>
                <div>
                  <dt className="text-xs text-neutral-500">Version</dt>
                  <dd className="text-neutral-100">{status.data.version}</dd>
                </div>
              </dl>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick actions</CardTitle>
            <CardDescription>Jump straight in</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2 text-sm">
            <Link className="text-neutral-300 hover:text-white" href="/chat">
              Talk to Victoria &rarr;
            </Link>
            <Link className="text-neutral-300 hover:text-white" href="/tasks">
              Review tasks &rarr;
            </Link>
            <Link className="text-neutral-300 hover:text-white" href="/email">
              Check email &rarr;
            </Link>
            <Link className="text-neutral-300 hover:text-white" href="/memory">
              What Victoria remembers &rarr;
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
