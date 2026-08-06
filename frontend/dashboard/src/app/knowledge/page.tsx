"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Search, Trash2, Upload } from "lucide-react";
import { useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, LoadingState } from "@/components/ui/state";
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";

export default function KnowledgePage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<{ answer: string; sources: string[] } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const documents = useQuery({ queryKey: ["knowledge", "documents"], queryFn: api.knowledge.list });

  const upload = useMutation({
    mutationFn: (file: File) => api.knowledge.upload(file),
    onSuccess: (summary) => {
      toast({
        title: "Document ingested",
        description: `${summary.filename} · ${summary.chunk_count} chunks`,
        variant: "success",
      });
      queryClient.invalidateQueries({ queryKey: ["knowledge", "documents"] });
    },
    onError: (error) => {
      toast({ title: "Upload failed", description: String(error), variant: "error" });
    },
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.knowledge.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["knowledge", "documents"] }),
  });

  const ask = useMutation({
    mutationFn: (q: string) => api.knowledge.ask(q),
    onSuccess: (result) => setAnswer(result),
    onError: () => {
      toast({ title: "Could not answer", description: "Try again in a moment.", variant: "error" });
    },
  });

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:px-8">
      <h1 className="text-xl font-semibold text-[var(--foreground)]">Knowledge</h1>
      <p className="mb-6 text-sm text-[var(--muted)]">
        Upload documents, then ask Victoria questions about them (retrieval-augmented generation).
      </p>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Ask your documents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="What does my document say about…"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && question.trim()) ask.mutate(question);
              }}
            />
            <Button onClick={() => ask.mutate(question)} disabled={!question.trim() || ask.isPending}>
              <Search className="size-4" /> Ask
            </Button>
          </div>
          {ask.isPending && <LoadingState label="Searching your documents…" />}
          {answer && (
            <div className="mt-4 rounded-xl border border-[var(--border)] bg-white/[0.02] p-4">
              <p className="text-sm text-[var(--foreground)]">{answer.answer}</p>
              {answer.sources.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {answer.sources.map((source) => (
                    <Badge key={source} variant="outline">
                      {source}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>Documents</CardTitle>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) upload.mutate(file);
              e.target.value = "";
            }}
          />
          <Button size="sm" onClick={() => fileInputRef.current?.click()} disabled={upload.isPending}>
            <Upload className="size-4" /> {upload.isPending ? "Uploading…" : "Upload"}
          </Button>
        </CardHeader>
        <CardContent className="space-y-2">
          {documents.isLoading && <LoadingState />}
          {documents.data?.documents.length === 0 && (
            <EmptyState
              icon={FileText}
              title="No documents yet"
              description="Upload a PDF, Word, PowerPoint, Excel, text file, or image (OCR) to get started."
            />
          )}
          {documents.data?.documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-white/[0.02] px-3 py-2.5"
            >
              <div className="flex items-center gap-3">
                <FileText className="size-4 text-[var(--accent)]" />
                <div>
                  <p className="text-sm font-medium text-[var(--foreground)]">{doc.filename}</p>
                  <p className="text-xs text-[var(--muted)]">
                    {doc.char_count.toLocaleString()} chars · {doc.chunk_count} chunks
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={() => remove.mutate(doc.id)}>
                <Trash2 className="size-4" />
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
