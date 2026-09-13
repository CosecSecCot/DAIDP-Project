"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { useSearchParams } from "next/navigation"
import {
  Activity,
  ArrowRight,
  ArrowUp,
  CalendarDays,
  Check,
  ChevronDown,
  CircleHelp,
  FileText,
  HeartPulse,
  LoaderCircle,
  Mic,
  Paperclip,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  X,
} from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { MarkdownText } from "@/components/markdown-text"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Bubble, BubbleContent } from "@/components/ui/bubble"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "@/components/ui/input-group"
import {
  Message,
  MessageAvatar,
  MessageContent,
  MessageHeader,
} from "@/components/ui/message"
import {
  MessageScroller,
  MessageScrollerButton,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/ui/message-scroller"

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"
type ChatMessage = { role: "user" | "assistant"; content: string }
type DocumentRecord = {
  id: string
  filename: string
  processing_status: "queued" | "processing" | "ready" | "failed"
  created_at: string
}
type Doctor = { id: number; name: string; specialty: string; clinic?: string }
type Slot = {
  id: number
  starts_at: string
  duration_minutes: number
  visit_type: string
}
type AgentResponse = {
  conversation_id: string
  document_ids?: string[]
  message?: string
  intake_summary?: string
  guidance?: {
    urgency?: string
    preliminary_steps?: string
    disclaimer?: string
  } | null
  doctor_recommendations?: Doctor[]
  available_slots?: Slot[]
  messages?: ChatMessage[]
}
const suggestions = [
  {
    icon: Activity,
    title: "Talk about a health concern",
    description:
      "Describe what’s bothering you and we’ll take it one step at a time.",
    message:
      "I’m not feeling well and would like help figuring out what to do.",
  },
  {
    icon: Stethoscope,
    title: "Find a doctor",
    description: "Share what kind of care you’re looking for.",
    message: "Can you help me find the right kind of doctor for my concern?",
  },
  {
    icon: FileText,
    title: "Understand a document",
    description: "Ask a question about a report or medical note.",
    message: "I have a medical document I’d like help understanding.",
  },
]
const dateLabel = (value: string) =>
  new Intl.DateTimeFormat("en", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value))

async function apiRequest<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !(init.body instanceof FormData))
    headers.set("Content-Type", "application/json")
  const result = await fetch(`${API_URL}${path}`, { ...init, headers })
  if (!result.ok) {
    const detail = (await result.json().catch(() => null)) as {
      detail?: string
    } | null
    throw new Error(detail?.detail ?? `Request failed (${result.status})`)
  }
  return result.json() as Promise<T>
}

export default function AssistantPage() {
  const searchParams = useSearchParams()
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [documentIds, setDocumentIds] = useState<string[]>([])
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [response, setResponse] = useState<AgentResponse | null>(null)
  const [draft, setDraft] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [uploading, setUploading] = useState(false)
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [loadingDocuments, setLoadingDocuments] = useState(true)
  const [documentsError, setDocumentsError] = useState("")
  const fileInput = useRef<HTMLInputElement>(null)
  const attachMenu = useRef<HTMLDetailsElement>(null)

  const loadDocuments = useCallback(async () => {
    try {
      const records = await apiRequest<DocumentRecord[]>("/documents")
      setDocuments(records)
      setDocumentsError("")
    } catch (cause) {
      setDocumentsError(
        cause instanceof Error ? cause.message : "Could not load documents."
      )
    } finally {
      setLoadingDocuments(false)
    }
  }, [])

  useEffect(() => {
    void loadDocuments()
    const timer = window.setInterval(() => void loadDocuments(), 3000)
    return () => window.clearInterval(timer)
  }, [loadDocuments])

  useEffect(() => {
    const id = searchParams.get("conversation_id")
    if (searchParams.has("new")) {
      const frame = requestAnimationFrame(() => {
        setConversationId(null)
        setDocumentIds([])
        setResponse(null)
        setMessages([])
        setDraft("")
        setError("")
        setNotice("")
      })
      return () => cancelAnimationFrame(frame)
    }
    if (!id) return
    let active = true
    void apiRequest<AgentResponse>(`/conversations/${id}`)
      .then((data) => {
        if (active) {
          setConversationId(id)
          setDocumentIds(data.document_ids ?? [])
          setResponse(data)
          setMessages(data.messages ?? [])
        }
      })
      .catch((cause: unknown) => {
        if (active)
          setError(
            cause instanceof Error
              ? cause.message
              : "Could not load conversation."
          )
      })
    return () => {
      active = false
    }
  }, [searchParams])

  async function sendMessage(text = draft) {
    const content = text.trim()
    if (!content || loading) return
    setDraft("")
    setError("")
    setNotice("")
    setLoading(true)
    const next = [...messages, { role: "user" as const, content }]
    setMessages(next)
    try {
      const data = await apiRequest<AgentResponse>(
        conversationId
          ? `/conversations/${conversationId}/messages`
          : "/conversations",
        {
          method: "POST",
          body: JSON.stringify({ message: content, document_ids: documentIds }),
        }
      )
      setConversationId(data.conversation_id)
      setDocumentIds(data.document_ids ?? documentIds)
      setResponse(data)
      setMessages([
        ...next,
        {
          role: "assistant",
          content:
            data.message ?? "I’m here to help. What else can you tell me?",
        },
      ])
    } catch (err) {
      setMessages(next)
      setError(
        err instanceof Error
          ? err.message
          : "Could not reach the MediQare service."
      )
    } finally {
      setLoading(false)
    }
  }
  async function uploadDocument(file?: File) {
    if (!file) return
    setUploading(true)
    setError("")
    setNotice("")
    const form = new FormData()
    form.append("file", file)
    try {
      const uploaded = await apiRequest<{
        id: string
        filename: string
        processing_status: string
      }>("/documents", { method: "POST", body: form })
      setDocumentIds((current) =>
        current.includes(uploaded.id) ? current : [...current, uploaded.id]
      )
      setNotice(
        `${uploaded.filename} uploaded. It will be attached when processing finishes.`
      )
      await loadDocuments()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.")
    } finally {
      setUploading(false)
      if (fileInput.current) fileInput.current.value = ""
    }
  }

  return (
    <section className="flex h-[calc(100svh-4rem)] min-h-0 min-w-0 flex-1 flex-col overflow-hidden px-4 md:px-8 xl:px-12">
      {!messages.length ? (
        <div className="mx-auto w-full max-w-4xl flex-1 py-6 md:py-10">
          <Empty className="min-h-0 border-0 p-0 text-left">
            <EmptyContent className="max-w-none items-stretch pt-6">
              <div className="mx-auto flex w-full max-w-4xl items-center justify-between gap-4 py-6 md:py-8">
                <div className="grid gap-2">
                  <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
                    {messages.length
                      ? "I’m here with you."
                      : "Good to see you."}
                  </h1>
                  <p className="text-base text-muted-foreground">
                    {messages.length
                      ? "Take your time. We’ll work through this together."
                      : "What would you like help with today?"}
                  </p>
                </div>
                <span className="hidden size-12 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary sm:grid">
                  <HeartPulse />
                </span>
              </div>
              <h2 className="text-base font-medium">Choose a place to start</h2>
              <div className="grid w-full gap-3 md:grid-cols-3">
                {suggestions.map(
                  ({ icon: Icon, title, description, message }) => (
                    <Button
                      key={title}
                      variant="outline"
                      className="group h-auto min-h-40 flex-col items-start justify-between gap-5 rounded-xl p-5 text-left whitespace-normal"
                      onClick={() => void sendMessage(message)}
                    >
                      <span className="grid gap-4">
                        <span className="grid size-10 place-items-center rounded-lg bg-primary/10 text-primary">
                          <Icon className="size-5" />
                        </span>
                        <span className="grid gap-1.5">
                          <span className="text-base font-semibold">
                            {title}
                          </span>
                          <span className="text-sm leading-relaxed text-muted-foreground">
                            {description}
                          </span>
                        </span>
                      </span>
                      <span className="flex w-full items-center justify-between text-sm font-medium">
                        Get started{" "}
                        <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
                      </span>
                    </Button>
                  )
                )}
              </div>
              <p className="flex items-start gap-2 text-sm leading-relaxed text-muted-foreground">
                <ShieldCheck className="mt-0.5 size-4 shrink-0" />I can share
                general health information, but I’m not a substitute for
                professional medical care.
              </p>
            </EmptyContent>
          </Empty>
        </div>
      ) : (
        <MessageScrollerProvider autoScroll defaultScrollPosition="end">
          <MessageScroller className="mx-auto w-full max-w-4xl max-h-[calc(100vh-264px)]">
            <MessageScrollerViewport className="h-0 min-h-0 flex-1">
              <MessageScrollerContent className="px-1 py-6">
                {messages.map((message, index) => (
                  <MessageScrollerItem
                    key={`${conversationId}-${index}`}
                    messageId={`${conversationId}-${index}`}
                    scrollAnchor={message.role === "user"}
                  >
                    <Message align={message.role === "user" ? "end" : "start"}>
                      <MessageAvatar>
                        <Avatar>
                          <AvatarFallback>
                            {message.role === "user" ? (
                              "Y"
                            ) : (
                              <HeartPulse />
                            )}
                          </AvatarFallback>
                        </Avatar>
                      </MessageAvatar>
                      <MessageContent className="max-w-[min(85%,42rem)]">
                        <MessageHeader className="text-sm">
                          {message.role === "assistant"
                            ? "MediQare assistant"
                            : "You"}
                        </MessageHeader>
                        <Bubble
                          align={message.role === "user" ? "end" : "start"}
                          variant={
                            message.role === "user" ? "default" : "muted"
                          }
                        >
                          <BubbleContent className="text-base">
                            {message.role === "assistant" ? (
                              <MarkdownText>{message.content}</MarkdownText>
                            ) : (
                              message.content
                            )}
                          </BubbleContent>
                        </Bubble>
                        {message.role === "assistant" &&
                          index === messages.length - 1 &&
                          response?.guidance && (
                            <Card>
                              <CardHeader>
                                <div className="flex flex-wrap items-center justify-between gap-3">
                                  <CardTitle className="text-lg">
                                    Preliminary guidance
                                  </CardTitle>
                                  {response.guidance.urgency && (
                                    <Badge variant="secondary">
                                      {response.guidance.urgency}
                                    </Badge>
                                  )}
                                </div>
                                <CardDescription className="text-base">
                                  For discussion with a qualified healthcare
                                  professional.
                                </CardDescription>
                              </CardHeader>
                              <CardContent className="grid gap-3 text-base leading-relaxed">
                                {response.intake_summary && (
                                  <p>
                                    <strong>What I understand:</strong>{" "}
                                    {response.intake_summary}
                                  </p>
                                )}
                                {response.guidance.preliminary_steps && (
                                  <p>{response.guidance.preliminary_steps}</p>
                                )}
                                {response.guidance.disclaimer && (
                                  <p className="text-muted-foreground">
                                    {response.guidance.disclaimer}
                                  </p>
                                )}
                              </CardContent>
                            </Card>
                          )}
                        {message.role === "assistant" &&
                        index === messages.length - 1 &&
                        response?.doctor_recommendations?.length ? (
                          <Card>
                            <CardHeader>
                              <CardTitle className="text-lg">
                                Care team to consider
                              </CardTitle>
                              <CardDescription className="text-base">
                                Based on what you’ve shared so far.
                              </CardDescription>
                            </CardHeader>
                            <CardContent className="grid gap-3">
                              {response.doctor_recommendations
                                .slice(0, 3)
                                .map((doctor) => (
                                  <div
                                    key={doctor.id}
                                    className="flex flex-wrap items-center gap-3 rounded-lg border p-4"
                                  >
                                    <Avatar>
                                      <AvatarFallback>
                                        <Stethoscope />
                                      </AvatarFallback>
                                    </Avatar>
                                    <div className="min-w-40 flex-1">
                                      <p className="font-medium">
                                        Dr. {doctor.name}
                                      </p>
                                      <p className="text-sm text-muted-foreground">
                                        {doctor.specialty}
                                        {doctor.clinic
                                          ? ` · ${doctor.clinic}`
                                          : ""}
                                      </p>
                                    </div>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() =>
                                        void sendMessage(
                                          `Show available appointment times with Dr. ${doctor.name}.`
                                        )
                                      }
                                    >
                                      View times{" "}
                                      <ArrowRight data-icon="inline-end" />
                                    </Button>
                                  </div>
                                ))}
                            </CardContent>
                          </Card>
                        ) : null}
                        {message.role === "assistant" &&
                        index === messages.length - 1 &&
                        response?.available_slots?.length ? (
                          <Card>
                            <CardHeader>
                              <CardTitle className="text-lg">
                                Available appointment times
                              </CardTitle>
                              <CardDescription className="text-base">
                                Select a time to ask the assistant to book it.
                              </CardDescription>
                            </CardHeader>
                            <CardContent className="grid gap-2">
                              {response.available_slots
                                .slice(0, 4)
                                .map((slot) => (
                                  <Button
                                    key={slot.id}
                                    variant="outline"
                                    className="h-auto justify-start gap-4 p-3 text-left whitespace-normal"
                                    onClick={() =>
                                      void sendMessage(
                                        `Book slot ${slot.id}.`
                                      )
                                    }
                                  >
                                    <CalendarDays />
                                    <span className="grid flex-1 gap-1">
                                      <span className="font-medium">
                                        {dateLabel(slot.starts_at)}
                                      </span>
                                      <span className="text-sm text-muted-foreground">
                                        {slot.duration_minutes} min ·{" "}
                                        {slot.visit_type.replaceAll("_", " ")}
                                      </span>
                                    </span>
                                    <ArrowRight />
                                  </Button>
                                ))}
                            </CardContent>
                          </Card>
                        ) : null}
                      </MessageContent>
                    </Message>
                  </MessageScrollerItem>
                ))}
                {loading && (
                  <MessageScrollerItem messageId="thinking">
                    <Message align="start">
                      <MessageAvatar>
                        <Avatar>
                          <AvatarFallback>
                            <HeartPulse />
                          </AvatarFallback>
                        </Avatar>
                      </MessageAvatar>
                      <MessageContent>
                        <MessageHeader>Thinking</MessageHeader>
                        <Bubble variant="muted">
                          <BubbleContent className="flex items-center gap-2 text-base">
                            <LoaderCircle className="size-4 animate-spin" />
                            Thinking through this...
                          </BubbleContent>
                        </Bubble>
                      </MessageContent>
                    </Message>
                  </MessageScrollerItem>
                )}
              </MessageScrollerContent>
            </MessageScrollerViewport>
            <MessageScrollerButton />
          </MessageScroller>
        </MessageScrollerProvider>
      )}
      {(error || notice) && (
        <Alert
          className="mx-auto mb-3 w-full max-w-4xl"
          variant={error ? "destructive" : "default"}
        >
          {error ? <CircleHelp /> : <FileText />}
          <AlertTitle>{error ? "Something needs attention" : "Document uploaded"}</AlertTitle>
          <AlertDescription className="flex items-center justify-between gap-3">
            {error || notice}
            <Button
              size="icon-sm"
              variant="ghost"
              aria-label="Dismiss"
              onClick={() => {
                setError("")
                setNotice("")
              }}
            >
              <X />
            </Button>
          </AlertDescription>
        </Alert>
      )}
      <div className="mx-auto w-full max-w-4xl pt-2 pb-4">
        <InputGroup className="rounded-xl bg-card shadow-sm">
          <InputGroupTextarea
            aria-label="Message your health assistant"
            className="min-h-24 text-base"
            placeholder="Share what’s on your mind..."
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault()
                void sendMessage()
              }
            }}
          />
          <InputGroupAddon align="block-end" className="justify-between gap-3">
            <span className="flex items-center gap-2">
              <details ref={attachMenu} className="group/attach relative">
                <InputGroupButton
                  asChild
                  variant="ghost"
                  size="sm"
                >
                  <summary
                    aria-haspopup="menu"
                    aria-disabled={uploading}
                    className="list-none aria-disabled:pointer-events-none aria-disabled:opacity-50 [&::-webkit-details-marker]:hidden"
                    onClick={(event) => {
                      if (uploading) event.preventDefault()
                    }}
                  >
                    {uploading ? (
                      <LoaderCircle className="animate-spin" />
                    ) : (
                      <Paperclip />
                    )}
                    {uploading
                      ? "Uploading..."
                      : documentIds.length
                        ? `Attach (${documentIds.length})`
                        : "Attach"}
                    <ChevronDown className="size-3.5 opacity-70" />
                  </summary>
                </InputGroupButton>
                <div
                  role="menu"
                  aria-label="Attach a document"
                  className="absolute bottom-full left-0 z-50 mb-2 w-80 max-w-[calc(100vw-2rem)] overflow-hidden rounded-lg border bg-popover p-1 text-popover-foreground shadow-lg"
                >
                  <p className="px-2.5 py-2 text-xs font-medium text-muted-foreground">
                    Ready documents
                  </p>
                  <div className="max-h-56 overflow-y-auto">
                    {documents
                      .filter(
                        (document) => document.processing_status === "ready"
                      )
                      .map((document) => {
                        const selected = documentIds.includes(document.id)
                        return (
                          <button
                            key={document.id}
                            type="button"
                            role="menuitemcheckbox"
                            aria-checked={selected}
                            title={document.filename}
                            className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground"
                            onClick={() =>
                              setDocumentIds((current) =>
                                selected
                                  ? current.filter((id) => id !== document.id)
                                  : [...current, document.id]
                              )
                            }
                          >
                            <FileText className="size-4 shrink-0 text-muted-foreground" />
                            <span className="min-w-0 flex-1 truncate">
                              {document.filename}
                            </span>
                            {selected && <Check className="size-4 shrink-0" />}
                          </button>
                        )
                      })}
                    {!documents.some(
                      (document) => document.processing_status === "ready"
                    ) && (
                      <p className="px-2.5 py-2 text-sm text-muted-foreground">
                        {documentsError
                          ? "Could not load ready documents."
                          : loadingDocuments
                            ? "Loading documents..."
                            : documents.length
                              ? "Documents are still processing."
                              : "No documents yet."}
                      </p>
                    )}
                  </div>
                  {documentsError && (
                    <p className="px-2.5 py-1 text-xs text-destructive">
                      {documentsError}
                    </p>
                  )}
                  <div className="my-1 border-t" />
                  <button
                    type="button"
                    role="menuitem"
                    disabled={uploading}
                    className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
                    onClick={() => {
                      attachMenu.current?.removeAttribute("open")
                      fileInput.current?.click()
                    }}
                  >
                    {uploading ? (
                      <LoaderCircle className="size-4 animate-spin" />
                    ) : (
                      <Paperclip className="size-4" />
                    )}
                    Upload a document
                  </button>
                </div>
              </details>
              <InputGroupButton
                type="button"
                variant="ghost"
                size="icon-sm"
                aria-label="Voice input"
                onClick={() => setError("Voice input is coming soon.")}
              >
                <Mic />
              </InputGroupButton>
              <input
                ref={fileInput}
                type="file"
                accept="application/pdf,text/plain"
                hidden
                onChange={(event) =>
                  void uploadDocument(event.target.files?.[0])
                }
              />
            </span>
            <InputGroupButton
              variant="default"
              size="icon-sm"
              aria-label="Send message"
              disabled={!draft.trim() || loading}
              onClick={() => void sendMessage()}
            >
              {loading ? (
                <LoaderCircle className="animate-spin" />
              ) : (
                <ArrowUp />
              )}
            </InputGroupButton>
          </InputGroupAddon>
        </InputGroup>
        <p className="mt-3 flex flex-wrap items-center justify-between gap-2 text-sm text-muted-foreground">
          <span className="flex items-center gap-2">
            <Sparkles className="size-4 shrink-0" />
            AI can make mistakes. Your care team is the source of truth.
          </span>
          <span>Powered by MediQare AI</span>
        </p>
      </div>
    </section>
  )
}
