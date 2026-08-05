"use client";

import { useQuery } from "@tanstack/react-query";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    // Standard next-themes SSR-safe pattern: the resolved theme is only known
    // after mount, so we avoid rendering theme-dependent UI until then.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  const status = useQuery({ queryKey: ["system", "status"], queryFn: api.system.status });

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 md:px-8">
      <h1 className="text-xl font-semibold text-neutral-50">Settings</h1>
      <p className="mb-6 text-sm text-neutral-500">Preferences for the Victoria dashboard.</p>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Dark mode by default, matching Victoria&apos;s aesthetic.</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-2">
          {mounted && (
            <>
              <Button
                variant={theme === "dark" ? "default" : "outline"}
                size="sm"
                onClick={() => setTheme("dark")}
              >
                <Moon className="size-4" /> Dark
              </Button>
              <Button
                variant={theme === "light" ? "default" : "outline"}
                size="sm"
                onClick={() => setTheme("light")}
              >
                <Sun className="size-4" /> Light
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Backend</CardTitle>
          <CardDescription>Connection details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-1 text-sm text-neutral-400">
          <p>
            API URL:{" "}
            <code>{process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}</code>
          </p>
          <p>Environment: {status.data?.environment ?? "unknown"}</p>
          <p>Version: {status.data?.version ?? "unknown"}</p>
        </CardContent>
      </Card>
    </div>
  );
}
