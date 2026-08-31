import React from "react";

type FileAttachmentProps = {
  onFileSelected?: (file: File) => Promise<void>;
  disabled?: boolean;
};

export function FileAttachment({ onFileSelected, disabled = false }: FileAttachmentProps) {
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
        className={`flex h-10 items-center rounded border border-[#c5cfda] px-3 text-sm font-medium text-[#25313d] ${
          disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
        }`}
      >
        {disabled ? "Uploading..." : "Attach file"}
      </label>
    </>
  );
}
