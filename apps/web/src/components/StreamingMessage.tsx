import React from "react";
import type { ChatMessage } from "./workspace-data";
import { MarkdownContent } from "./MarkdownContent";

type StreamingMessageProps = {
  message: ChatMessage;
  compact?: boolean;
  onResubmit?: (messageId: string, content: string) => Promise<void>;
};

export function StreamingMessage({ message, compact = false, onResubmit }: StreamingMessageProps) {
  const [isEditing, setIsEditing] = React.useState(false);
  const [editedContent, setEditedContent] = React.useState(message.content);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  async function submitEdit() {
    const content = editedContent.trim();
    if (!content || !onResubmit) return;
    setIsSubmitting(true);
    try {
      await onResubmit(message.id, content);
      setIsEditing(false);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (compact) {
    const isUser = message.tone === "user";
    return (
      <article className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
        <div className={`max-w-[88%] ${isUser ? "rounded-2xl rounded-br-md bg-[#edf2f5] px-4 py-3" : "px-1 py-1"}`}>
          {!isUser ? <p className="mb-1 text-xs font-semibold text-[#176b5b]">ResearchOS</p> : null}
          {message.attachments?.length ? (
            <div className="mb-2 flex flex-wrap gap-2">
              {message.attachments.map((attachment) => (
                <div key={attachment.id} className="max-w-full rounded border border-[#c5cfda] bg-white px-2 py-1 text-xs">
                  <span className="truncate">{attachment.filename}</span>
                </div>
              ))}
            </div>
          ) : null}
          {isEditing ? (
            <div className="min-w-[240px]">
              <textarea
                aria-label="Edit prompt"
                value={editedContent}
                onChange={(event) => setEditedContent(event.target.value)}
                rows={4}
                className="w-full resize-y rounded-lg border border-[#9cabb9] bg-white p-2 text-sm leading-5 outline-none focus:border-[#176b5b]"
              />
              <div className="mt-2 flex justify-end gap-2">
                <button type="button" onClick={() => { setEditedContent(message.content); setIsEditing(false); }} className="rounded px-3 py-1.5 text-xs font-semibold text-[#536174] hover:bg-white">Cancel</button>
                <button type="button" disabled={isSubmitting} onClick={() => void submitEdit()} className="rounded bg-[#176b5b] px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60">{isSubmitting ? "Submitting..." : "Submit edit"}</button>
              </div>
            </div>
          ) : (
            <>
              <div className="text-sm leading-6 text-[#202124]">
                <MarkdownContent content={message.content} />
              </div>
              {isUser && onResubmit ? (
                <div className="mt-1 flex justify-end">
                  <button type="button" onClick={() => setIsEditing(true)} className="rounded px-2 py-1 text-xs font-semibold text-[#536174] hover:bg-white" aria-label="Edit prompt">Edit</button>
                </div>
              ) : null}
            </>
          )}
        </div>
      </article>
    );
  }

  const messageClass =
    message.tone === "user"
      ? "border-[#d7dde6] bg-[#f8fafc]"
      : message.tone === "assistant"
        ? "border-[#bfd8ce] bg-[#f4fbf7]"
        : "border-[#e0d2aa] bg-[#fff9ea]";

  return (
    <article className={message.tone === "user" ? "max-w-3xl" : "ml-auto max-w-3xl"}>
      <p className="mb-2 text-xs font-medium text-[#667386]">{message.author}</p>
      <div className={`rounded border p-4 text-sm leading-6 ${messageClass}`}>
        {message.attachments?.length ? (
          <div className="mb-3 flex flex-wrap gap-2">
            {message.attachments.map((attachment) => (
              <div
                key={attachment.id}
                className="flex max-w-full items-center gap-2 rounded border border-[#c5cfda] bg-white px-3 py-2"
              >
                <span className="rounded border border-[#e5b7b7] px-1.5 py-0.5 text-[10px] font-bold uppercase text-[#b42318]">
                  PDF
                </span>
                <span className="truncate text-xs font-medium text-[#25313d]">
                  {attachment.filename}
                </span>
              </div>
            ))}
          </div>
        ) : null}
        {message.content ? <MarkdownContent content={message.content} /> : null}
      </div>
    </article>
  );
}
