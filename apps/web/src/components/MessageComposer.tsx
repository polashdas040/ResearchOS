import React from "react";
import { FileAttachment } from "./FileAttachment";
import { HydrationSafeButton, HydrationSafeInput } from "./HydrationSafeControls";
import { AttachedFile } from "../lib/api-client";

type MessageComposerProps = {
  onSubmit: (content: string) => Promise<void>;
  onFileSelected?: (file: File) => Promise<void>;
  onOpenFile?: (fileId: string) => Promise<void>;
  isUploadingFile?: boolean;
  attachedFiles?: AttachedFile[];
  compact?: boolean;
};

export function MessageComposer({
  onSubmit,
  onFileSelected,
  onOpenFile,
  isUploadingFile = false,
  attachedFiles = [],
  compact = false
}: MessageComposerProps) {
  const [content, setContent] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const messageContent = content.trim();
    if (!messageContent && attachedFiles.length === 0) {
      return;
    }
    setIsSubmitting(true);
    setContent("");
    try {
      await onSubmit(messageContent);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className={compact ? "bg-transparent" : "border-t border-[#d7dde6] bg-[#f7f9fb] p-4"} onSubmit={handleSubmit}>
      <div className={`border border-[#b7c2cf] bg-white p-2 shadow-sm ${compact ? "rounded-2xl" : "rounded"}`}>
        {attachedFiles.length > 0 ? (
          <div className="mb-2 flex flex-wrap gap-2">
            {attachedFiles.map((file) => (
              <button
                key={file.id}
                type="button"
                onClick={() => void onOpenFile?.(file.id)}
                className="rounded border border-[#c5cfda] bg-[#f8fafc] px-3 py-2 text-xs font-medium text-[#25313d]"
              >
                <span>{file.filename}</span>
                <span className="ml-2 text-[#176b5b]">{file.status}</span>
              </button>
            ))}
          </div>
        ) : null}
        <div className={`flex gap-2 ${compact ? "items-center" : "flex-col sm:flex-row sm:items-center"}`}>
          <FileAttachment onFileSelected={onFileSelected} disabled={isUploadingFile} />
          <HydrationSafeInput
            className="min-h-10 min-w-0 flex-1 bg-transparent px-2 text-sm outline-none"
            placeholder="Ask ResearchOS..."
            value={content}
            onChange={(event) => setContent(event.target.value)}
          />
          <HydrationSafeButton
            type="submit"
            disabled={isSubmitting}
            aria-label="Send message"
            title="Send message"
            className={`h-10 bg-[#176b5b] text-sm font-semibold text-white disabled:opacity-60 ${compact ? "w-10 shrink-0 rounded-full px-0 text-lg" : "rounded px-4"}`}
          >
            {compact ? (isSubmitting ? "..." : "↑") : (isSubmitting ? "Sending..." : "Send message")}
          </HydrationSafeButton>
        </div>
      </div>
    </form>
  );
}
