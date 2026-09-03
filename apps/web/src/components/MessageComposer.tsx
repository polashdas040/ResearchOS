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
};

export function MessageComposer({
  onSubmit,
  onFileSelected,
  onOpenFile,
  isUploadingFile = false,
  attachedFiles = []
}: MessageComposerProps) {
  const [content, setContent] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!content.trim()) {
      return;
    }
    setIsSubmitting(true);
    try {
      await onSubmit(content.trim());
      setContent("");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="border-t border-[#d7dde6] bg-[#f7f9fb] p-4" onSubmit={handleSubmit}>
      <div className="rounded border border-[#b7c2cf] bg-white p-2">
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
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
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
            className="h-10 rounded bg-[#176b5b] px-4 text-sm font-semibold text-white"
          >
            {isSubmitting ? "Sending..." : "Send message"}
          </HydrationSafeButton>
        </div>
      </div>
    </form>
  );
}
