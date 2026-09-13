"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { FileText, LoaderCircle, Paperclip } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"
type DocumentRecord = {
  id: string
  filename: string
  processing_status: "queued" | "processing" | "ready" | "failed"
  created_at: string
}

export default function DocumentsPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [loading, setLoading] = useState(true)

  const loadDocuments = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/documents`)
      if (!response.ok) throw new Error("Could not load uploaded documents.")
      setDocuments((await response.json()) as DocumentRecord[])
      setError("")
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load documents.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadDocuments()
    const timer = window.setInterval(() => void loadDocuments(), 2000)
    return () => window.clearInterval(timer)
  }, [loadDocuments])

  async function upload(file?: File) {
    if (!file) return
    setUploading(true)
    setError("")
    setNotice("")
    const form = new FormData()
    form.append("file", file)
    try {
      const response = await fetch(`${API_URL}/documents`, {
        method: "POST",
        body: form,
      })
      if (!response.ok) throw new Error("Upload failed. Please try again.")
      setNotice("Document uploaded. Processing will finish shortly.")
      await loadDocuments()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Upload failed.")
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ""
    }
  }

  return (
    <section className="mx-auto w-full max-w-5xl flex-1 p-4 py-8 md:p-8 md:py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Documents</h1>
        <p className="mt-2 text-base text-muted-foreground">
          Reports and notes available to reference in conversations.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="ring-0 border border-dashed col-span-full mb-4">
          <CardContent className="flex min-h-24 items-center justify-between gap-4 p-5">
            <div>
              <p className="font-medium">Add a document</p>
              <p className="mt-1 text-sm text-muted-foreground">
                PDF or TXT files can be attached to chats.
              </p>
            </div>
            <Button
              variant="outline"
              disabled={uploading}
              onClick={() => inputRef.current?.click()}
            >
              {uploading ? (
                <LoaderCircle className="animate-spin" />
              ) : (
                <Paperclip />
              )}
              {uploading ? "Uploading..." : "Upload"}
            </Button>
            <input
              ref={inputRef}
              className="hidden"
              type="file"
              accept="application/pdf,text/plain"
              onChange={(event) => void upload(event.target.files?.[0])}
            />
          </CardContent>
        </Card>
        {loading && documents.length === 0 && (
          <p className="col-span-full text-sm text-muted-foreground">Loading documents…</p>
        )}
        {!loading && documents.length === 0 && !error && (
          <p className="col-span-full text-sm text-muted-foreground">No documents uploaded yet.</p>
        )}
        {documents.map((doc) => (
          <Card key={doc.id}>
            <CardContent className="flex items-center gap-4 p-5">
              <span className="grid size-11 place-items-center rounded-lg bg-primary/10 text-primary">
                <FileText />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{doc.filename}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {new Date(doc.created_at).toLocaleString()}
                </p>
              </div>
              <Badge variant={doc.processing_status === "failed" ? "destructive" : "secondary"}>
                {doc.processing_status === "ready" ? "Ready" : doc.processing_status === "failed" ? "Failed" : "Processing"}
              </Badge>
            </CardContent>
          </Card>
        ))}
      </div>
      {notice && (
        <p className="mt-4 text-sm text-emerald-600" role="status">
          {notice}
        </p>
      )}
      {error && (
        <p className="mt-4 text-sm text-muted-foreground" role="status">
          {error}
        </p>
      )}
    </section>
  )
}
