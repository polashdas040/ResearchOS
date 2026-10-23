import React from "react";

type FileAttachmentProps = {
  onFileSelected?: (file: File) => Promise<void>;
  disabled?: boolean;
  variant?: "button" | "source";
};

export function FileAttachment({
  onFileSelected,
  disabled = false,
  variant = "button"
}: FileAttachmentProps) {
  const inputId = React.useId();

  async function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !onFileSelected) {
      return;
    }
    await onFileSelected(file);
    event.target.value = "";
  }

  return (
    <>
      <input
        id={inputId}
        type="file"
        className="sr-only"
        onChange={handleChange}
        accept=".pdf,.csv,.json,.txt,.png,.jpg,.jpeg"
        disabled={disabled}
      />
      <label
        htmlFor={inputId}
        className={`${variant === "source"
          ? "flex min-h-16 items-center gap-3 rounded-lg border border-[#dedfe3] bg-[#fafafa] px-4 py-3 text-sm text-[#202124]"
          : "flex h-10 items-center rounded border border-[#c5cfda] px-3 text-sm font-medium text-[#25313d]"} ${
          disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
        }`}
      >
        {variant === "source" ? (
          <>
            <span className="flex h-9 w-9 items-center justify-center rounded bg-[#e8f2ef] font-bold text-[#176b5b]">+</span>
            <span className="min-w-0 flex-1">
              <span className="block font-medium">{disabled ? "Uploading source..." : "Import a research source"}</span>
              <span className="mt-0.5 block text-xs text-[#737780]">PDF, CSV, JSON, text, or image</span>
            </span>
            <span aria-hidden="true" className="text-[#8b8e95]">›</span>
          </>
        ) : disabled ? "Uploading..." : "Attach file"}
      </label>
    </>
  );
}
