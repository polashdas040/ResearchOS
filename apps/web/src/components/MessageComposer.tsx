import React from "react";
import { FileAttachment } from "./FileAttachment";
import { HydrationSafeButton, HydrationSafeInput } from "./HydrationSafeControls";

export function MessageComposer() {
  return (
    <form className="border-t border-[#d7dde6] bg-[#f7f9fb] p-4">
      <div className="flex flex-col gap-3 rounded border border-[#b7c2cf] bg-white p-2 sm:flex-row sm:items-center">
        <FileAttachment />
        <HydrationSafeInput
          className="min-h-10 min-w-0 flex-1 bg-transparent px-2 text-sm outline-none"
          placeholder="Ask ResearchOS..."
        />
        <HydrationSafeButton
          type="submit"
          className="h-10 rounded bg-[#176b5b] px-4 text-sm font-semibold text-white"
        >
          Send message
        </HydrationSafeButton>
      </div>
    </form>
  );
}
