import React from "react";

type FileAttachmentProps = {
  onFileSelected?: (file: File) => Promise<void>;
};

export function FileAttachment({ onFileSelected }: FileAttachmentProps) {
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
      />
      <label
        htmlFor={inputId}
        className="flex h-10 cursor-pointer items-center rounded border border-[#c5cfda] px-3 text-sm font-medium text-[#25313d]"
      >
        Attach file
      </label>
    </>
  );
}
