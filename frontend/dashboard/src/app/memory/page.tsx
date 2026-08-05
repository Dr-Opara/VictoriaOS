"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

export default function MemoryPage() {
  const [query, setQuery] = useState("");
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const queryClient = useQueryClient();

  const memories = useQuery({
    queryKey: ["memory", query],
    queryFn: () => api.memory.list(query || undefined),
  });

  const remember = useMutation({
    mutationFn: () => api.memory.remember(key, value),
    onSuccess: () => {
      setKey("");
      setValue("");
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    },
  });

  const forget = useMutation({
    mutationFn: (memoryKey: string) => api.memory.forget(memoryKey),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["memory"] }),
  });

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-8">
      <h1 className="text-xl font-semibold text-neutral-50">Memory</h1>
      <p className="mb-6 text-sm text-neutral-500">
        Everything Victoria remembers about you and your preferences.
      </p>

      <Card className="mb-6">
        <CardContent className="grid grid-cols-1 gap-2 pt-5 sm:grid-cols-[1fr_1fr_auto]">
          <Input placeholder="Key (e.g. favorite airline)" value={key} onChange={(e) => setKey(e.target.value)} />
          <Input placeholder="Value (e.g. United)" value={value} onChange={(e) => setValue(e.target.value)} />
          <Button
            onClick={() => remember.mutate()}
            disabled={!key.trim() || !value.trim() || remember.isPending}
          >
            Remember
          </Button>
        </CardContent>
      </Card>

      <Input
        placeholder="Search memories…"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        className="mb-4"
      />

      <div className="space-y-2">
        {memories.data?.memories.map((memory) => (
          <Card key={`${memory.key}-${memory.created_at}`}>
            <CardContent className="flex items-center justify-between pt-4">
              <div>
                <p className="text-sm font-medium text-neutral-100">{memory.key}</p>
                <p className="text-sm text-neutral-400">{memory.value}</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => forget.mutate(memory.key)}
                aria-label={`Forget ${memory.key}`}
              >
                <Trash2 className="size-4" />
              </Button>
            </CardContent>
          </Card>
        ))}
        {memories.data?.memories.length === 0 && (
          <p className="text-sm text-neutral-500">Nothing remembered yet.</p>
        )}
      </div>
    </div>
  );
}
