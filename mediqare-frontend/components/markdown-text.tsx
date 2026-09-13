type MarkdownTextProps = { children: string }

function inlineMarkdown(text: string) {
  return text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={index}>{part.slice(1, -1)}</em>
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index} className="rounded bg-background/60 px-1 py-0.5 text-[0.9em]">{part.slice(1, -1)}</code>
    }
    return part
  })
}

export function MarkdownText({ children }: MarkdownTextProps) {
  return (
    <div className="space-y-2 whitespace-normal">
      {children.split("\n").map((line, index) => {
        const heading = line.match(/^#{1,3}\s+(.+)$/)
        const listItem = line.match(/^\s*[-*]\s+(.+)$/)
        const numberedItem = line.match(/^\s*\d+\.\s+(.+)$/)

        if (!line.trim()) return <div key={index} className="h-1" />
        if (heading) {
          return <h3 key={index} className="font-semibold">{inlineMarkdown(heading[1])}</h3>
        }
        if (listItem || numberedItem) {
          return (
            <div key={index} className="flex gap-2 pl-1">
              <span aria-hidden="true">{numberedItem ? "•" : "•"}</span>
              <span>{inlineMarkdown((listItem ?? numberedItem)![1])}</span>
            </div>
          )
        }
        return <p key={index}>{inlineMarkdown(line)}</p>
      })}
    </div>
  )
}
