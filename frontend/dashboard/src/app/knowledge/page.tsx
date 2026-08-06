"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Search, Trash2, Upload, X } from "lucide-react";
import type React from "react";
import { useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, LoadingState, SkeletonText } from "@/components/ui/state";
import { Input } from "@/components/ui/input";
import { MarkdownMessage } from "@/components/ui/markdown";
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";

const ACCEPTED_DOCUMENTS = [
  ".txt",
  ".md",
  ".csv",
  ".pdf",
  ".docx",
  ".pptx",
  ".xlsx",
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
  ".tif",
  ".tiff",
].join(",");

export default function KnowledgePage() {
  const [question, setQuestion] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const documents = useQuery({
    queryKey: ["knowledge", "documents"],
    queryFn: api.knowledge.list,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["knowledge", "documents"] });

  const upload = useMutation({
    mutationFn: (file: File) =>
      api.knowledge.upload(file, {
        onProgress: setUploadProgress,
      }),
    onMutate: () => setUploadProgress(0),
    onSuccess: (summary) => {
      toast({
        title: "Document ingested",
        description: `${summary.filename} - ${summary.chunk_count} chunks`,
        variant: "success",
      });
      setUploadProgress(null);
      invalidate();
    },
    onError: (error) => {
      setUploadProgress(null);
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Try a supported document.",
        variant: "error",
      });
    },
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.knowledge.remove(id),
    onSuccess: () => {
      invalidate();
      toast({ title: "Document deleted", variant: "success" });
    },
    onError: (error) => {
      toast({
        title: "Could not delete document",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const search = useMutation({
    mutationFn: (q: string) => api.knowledge.search(q, 8),
    onError: (error) => {
      toast({
        title: "Search failed",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const ask = useMutation({
    mutationFn: (q: string) => api.knowledge.ask(q, 6),
    onError: (error) => {
      toast({
        title: "Could not answer",
        description: error instanceof Error ? error.message : "Try again shortly.",
        variant: "error",
      });
    },
  });

  const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) upload.mutate(file);
    event.target.value = "";
  };

  const submitSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!searchTerm.trim()) return;
    search.mutate(searchTerm.trim());
  };

  const submitAsk = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!question.trim()) return;
    ask.mutate(question.trim());
  };

  const docs = documents.data?.documents ?? [];
  const hasDocuments = docs.length > 0;

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 md:px-8">
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--foreground)]">Knowledge</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Upload supported documents, search their chunks, and ask source-cited questions.
          </p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_DOCUMENTS}
          className="hidden"
          onChange={handleUpload}
        />
        <Button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={upload.isPending}
        >
          <Upload className="size-4" /> {upload.isPending ? "Uploading" : "Upload"}
        </Button>
      </div>

      {uploadProgress !== null && (
        <div className="mb-4 rounded-lg border border-[var(--border)] bg-white/[0.025] p-3">
          <div className="mb-2 flex items-center justify-between text-xs">
            <span className="text-[var(--muted)]">Upload progress</span>
            <span className="text-[var(--foreground)]">{uploadProgress}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-white/[0.06]">
            <div
              className="h-full rounded-full bg-[var(--accent)] transition-[width]"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_0.9fr]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Ask Documents</CardTitle>
              <CardDescription>Answers are generated from retrieved document excerpts.</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="flex flex-col gap-2 sm:flex-row" onSubmit={submitAsk}>
                <Input
                  placeholder="What do my documents say about..."
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  disabled={!hasDocuments || ask.isPending}
                  aria-label="Ask a document question"
                />
                <Button type="submit" disabled={!question.trim() || !hasDocuments || ask.isPending}>
                  <Search className="size-4" /> Ask
                </Button>
              </form>
              {!hasDocuments && (
                <p className="mt-3 text-xs text-[var(--muted)]">
                  Upload a document before asking a knowledge question.
                </p>
              )}
              {ask.isPending && <LoadingState label="Searching and answering..." />}
              {ask.data && (
                <div className="mt-4 rounded-lg border border-[var(--border)] bg-white/[0.025] p-4">
                  <MarkdownMessage content={ask.data.answer} />
                  {ask.data.sources.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {ask.data.sources.map((source) => (
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
            <CardHeader>
              <CardTitle>Search Documents</CardTitle>
              <CardDescription>Semantic search over ingested chunks.</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="flex flex-col gap-2 sm:flex-row" onSubmit={submitSearch}>
                <Input
                  placeholder="Search document text..."
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  disabled={!hasDocuments || search.isPending}
                  aria-label="Search documents"
                />
                {searchTerm && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => setSearchTerm("")}
                    aria-label="Clear document search"
                  >
                    <X className="size-4" />
                  </Button>
                )}
                <Button type="submit" disabled={!searchTerm.trim() || !hasDocuments || search.isPending}>
                  Search
                </Button>
              </form>
              {search.isPending && <LoadingState label="Searching documents..." />}
              {search.data && search.data.results.length === 0 && (
                <p className="mt-4 text-sm text-[var(--muted)]">No matching document chunks.</p>
              )}
              {search.data && search.data.results.length > 0 && (
                <div className="mt-4 space-y-3">
                  {search.data.results.map((result) => (
                    <div
                      key={result.chunk_id}
                      className="rounded-lg border border-[var(--border)] bg-white/[0.025] p-3"
                    >
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <Badge variant="outline">Doc {result.document_id}</Badge>
                        <span className="text-xs text-[var(--muted)]">
                          Score {result.score.toFixed(3)}
                        </span>
                      </div>
                      <p className="text-sm leading-relaxed text-[var(--foreground)]/90">
                        {result.text}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Documents</CardTitle>
              <CardDescription>{docs.length} ingested document(s)</CardDescription>
            </div>
            <FileText className="size-5 text-[var(--accent)]" />
          </CardHeader>
          <CardContent className="space-y-2">
            {documents.isLoading && <SkeletonText lines={6} />}
            {documents.isError && (
              <ErrorState
                title="Documents unavailable"
                description="Victoria could not list ingested documents."
                action={
                  <Button size="sm" variant="outline" onClick={() => documents.refetch()}>
                    Retry
                  </Button>
                }
              />
            )}
            {documents.isSuccess && docs.length === 0 && (
              <EmptyState
                icon={FileText}
                title="No documents yet"
                description="Upload a supported file to build Victoria's knowledge base."
              />
            )}
            {docs.map((doc) => (
              <div
                key={doc.id}
                className="flex items-start justify-between gap-3 rounded-lg border border-[var(--border)] bg-white/[0.025] p-3"
              >
                <div className="min-w-0">
                  <p className="break-words text-sm font-medium text-[var(--foreground)]">
                    {doc.filename}
                  </p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    {doc.char_count.toLocaleString()} chars - {doc.chunk_count} chunks
                  </p>
                  {doc.content_type && (
                    <Badge variant="outline" className="mt-2">
                      {doc.content_type}
                    </Badge>
                  )}
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => remove.mutate(doc.id)}
                  disabled={remove.isPending}
                  aria-label={`Delete ${doc.filename}`}
                >
                  <Trash2 className="size-4" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
