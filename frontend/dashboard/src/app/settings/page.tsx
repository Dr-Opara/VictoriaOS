"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bot,
  CheckCircle2,
  Database,
  HardDrive,
  Headphones,
  Info,
  Mail,
  Mic,
  Moon,
  Palette,
  Radio,
  Settings2,
  Sun,
  Volume2,
} from "lucide-react";
import Link from "next/link";
import type React from "react";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SkeletonText } from "@/components/ui/state";
import { api } from "@/lib/api";

const DASHBOARD_VERSION = "0.2.0";

interface AudioDeviceState {
  mediaSupported: boolean;
  outputSelectionSupported: boolean;
  loading: boolean;
  microphones: number;
  speakers: number;
}

function SettingRow({
  icon: Icon,
  label,
  value,
  badge,
}: {
  icon: typeof Bot;
  label: string;
  value: string;
  badge?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-[var(--border)] bg-white/[0.025] px-3 py-2.5">
      <div className="flex min-w-0 items-center gap-2">
        <Icon className="size-4 shrink-0 text-[var(--accent)]" />
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-[var(--foreground)]">{label}</p>
          <p className="truncate text-xs text-[var(--muted)]">{value}</p>
        </div>
      </div>
      {badge}
    </div>
  );
}

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [audioDevices, setAudioDevices] = useState<AudioDeviceState>({
    mediaSupported: false,
    outputSelectionSupported: false,
    loading: true,
    microphones: 0,
    speakers: 0,
  });

  useEffect(() => {
    queueMicrotask(() => setMounted(true));
  }, []);

  useEffect(() => {
    const refreshDevices = async () => {
      if (!navigator.mediaDevices?.enumerateDevices) {
        setAudioDevices({
          mediaSupported: false,
          outputSelectionSupported: false,
          loading: false,
          microphones: 0,
          speakers: 0,
        });
        return;
      }

      const devices = await navigator.mediaDevices.enumerateDevices();
      setAudioDevices({
        mediaSupported: true,
        outputSelectionSupported: "setSinkId" in HTMLMediaElement.prototype,
        loading: false,
        microphones: devices.filter((device) => device.kind === "audioinput").length,
        speakers: devices.filter((device) => device.kind === "audiooutput").length,
      });
    };

    refreshDevices().catch(() =>
      setAudioDevices((prev) => ({ ...prev, mediaSupported: false, loading: false })),
    );

    navigator.mediaDevices?.addEventListener?.("devicechange", refreshDevices);
    return () => navigator.mediaDevices?.removeEventListener?.("devicechange", refreshDevices);
  }, []);

  const status = useQuery({
    queryKey: ["system", "status"],
    queryFn: api.system.status,
    refetchInterval: 10_000,
  });

  const health = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 10_000,
  });

  const usage = useQuery({
    queryKey: ["system", "usage"],
    queryFn: api.system.usage,
    refetchInterval: 15_000,
  });

  const email = useQuery({
    queryKey: ["email", "unread", 1],
    queryFn: () => api.email.unread(1),
    refetchInterval: 30_000,
  });

  const voice = useQuery({
    queryKey: ["voice", "connect"],
    queryFn: api.voice.connect,
    refetchInterval: 30_000,
  });

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 md:px-8">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-[var(--foreground)]">Settings</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          v0.2 dashboard configuration and connection status.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="size-4 text-[var(--accent)]" /> Appearance
            </CardTitle>
            <CardDescription>Local dashboard theme preference.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {mounted && (
              <>
                <Button
                  type="button"
                  variant={theme === "dark" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTheme("dark")}
                >
                  <Moon className="size-4" /> Dark
                </Button>
                <Button
                  type="button"
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
            <CardTitle className="flex items-center gap-2">
              <Bot className="size-4 text-[var(--accent)]" /> OpenAI
            </CardTitle>
            <CardDescription>Status reported through the backend system endpoint.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {status.isLoading && <SkeletonText lines={3} />}
            {status.isError && (
              <ErrorState
                title="Backend status unavailable"
                description="OpenAI model status could not be read from the backend."
              />
            )}
            {status.data && (
              <>
                <SettingRow
                  icon={Bot}
                  label="Model"
                  value={status.data.model}
                  badge={<Badge variant="success">Configured</Badge>}
                />
                <SettingRow
                  icon={HardDrive}
                  label="Environment"
                  value={status.data.environment}
                  badge={<Badge variant="outline">{status.data.status}</Badge>}
                />
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="size-4 text-[var(--accent)]" /> Yahoo Mail
            </CardTitle>
            <CardDescription>Connection state from `/email/unread`.</CardDescription>
          </CardHeader>
          <CardContent>
            <SettingRow
              icon={Mail}
              label="Yahoo Mail"
              value={
                email.isLoading
                  ? "Checking"
                  : email.data?.configured
                    ? "Backend can read unread mail"
                    : "Not configured"
              }
              badge={
                <Badge variant={email.data?.configured ? "success" : email.isError ? "destructive" : "warning"}>
                  {email.isLoading ? "Checking" : email.data?.configured ? "Connected" : "Offline"}
                </Badge>
              }
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Radio className="size-4 text-[var(--accent)]" /> Raspberry Pi
            </CardTitle>
            <CardDescription>Voice-node handshake endpoint exposed by the backend.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <SettingRow
              icon={Radio}
              label="Voice handshake"
              value={voice.isLoading ? "Checking" : voice.isSuccess ? "Available" : "Unavailable"}
              badge={
                <Badge variant={voice.isSuccess ? "success" : voice.isError ? "warning" : "outline"}>
                  {voice.isLoading ? "Checking" : voice.isSuccess ? "Ready" : "No signal"}
                </Badge>
              }
            />
            <SettingRow
              icon={Settings2}
              label="Wake word"
              value={voice.data?.wake_word ?? "Unavailable"}
            />
            <SettingRow
              icon={Headphones}
              label="Audio format"
              value={
                voice.data
                  ? `${voice.data.sample_rate} Hz, ${voice.data.channels} channel, ${voice.data.encoding}`
                  : "Unavailable"
              }
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mic className="size-4 text-[var(--accent)]" /> Microphone And Speaker
            </CardTitle>
            <CardDescription>Browser-visible local audio device status.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <SettingRow
              icon={Mic}
              label="Microphone"
              value={
                audioDevices.loading
                  ? "Checking"
                  : audioDevices.mediaSupported
                    ? `${audioDevices.microphones} input device(s)`
                    : "Media devices unavailable"
              }
              badge={
                <Badge variant={audioDevices.microphones > 0 ? "success" : "warning"}>
                  {audioDevices.loading ? "Checking" : audioDevices.microphones > 0 ? "Detected" : "Unavailable"}
                </Badge>
              }
            />
            <SettingRow
              icon={Volume2}
              label="Speaker"
              value={
                audioDevices.loading
                  ? "Checking"
                  : audioDevices.outputSelectionSupported
                    ? `${audioDevices.speakers} output device(s)`
                    : "Output selection not exposed"
              }
              badge={
                <Badge variant={audioDevices.outputSelectionSupported ? "success" : "outline"}>
                  {audioDevices.outputSelectionSupported ? "Detected" : "Browser limited"}
                </Badge>
              }
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="size-4 text-[var(--accent)]" /> Memory Controls
            </CardTitle>
            <CardDescription>Memory count and available v0.2 actions.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <SettingRow
              icon={Database}
              label="Stored memories"
              value={usage.data ? `${usage.data.memories_stored}` : usage.isError ? "Unavailable" : "Checking"}
              badge={<Badge variant={usage.isSuccess ? "success" : "outline"}>Backend</Badge>}
            />
            <div className="flex flex-wrap gap-2">
              <Button asChild variant="outline" size="sm">
                <Link href="/memory">Open Memory</Link>
              </Button>
              <Button type="button" variant="outline" size="sm" disabled>
                Clear all unavailable
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="size-4 text-[var(--accent)]" /> About
            </CardTitle>
            <CardDescription>VictoriaOS v0.2 dashboard release.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-2 md:grid-cols-2">
            <SettingRow
              icon={CheckCircle2}
              label="Dashboard version"
              value={DASHBOARD_VERSION}
              badge={<Badge variant="success">v0.2</Badge>}
            />
            <SettingRow
              icon={HardDrive}
              label="Backend version"
              value={health.data?.version ?? status.data?.version ?? "Unavailable"}
              badge={<Badge variant={health.isSuccess ? "success" : "outline"}>API</Badge>}
            />
            <SettingRow
              icon={HardDrive}
              label="API URL"
              value={process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            />
            <SettingRow
              icon={HardDrive}
              label="Service health"
              value={health.isLoading ? "Checking" : health.isSuccess ? health.data.status : "Unavailable"}
              badge={
                <Badge variant={health.isSuccess ? "success" : health.isError ? "destructive" : "outline"}>
                  {health.isSuccess ? "Healthy" : health.isError ? "Error" : "Checking"}
                </Badge>
              }
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
