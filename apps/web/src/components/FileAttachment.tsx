import React from "react";
import { HydrationSafeButton } from "./HydrationSafeControls";

export function FileAttachment() {
  return (
    <HydrationSafeButton
      type="button"
      className="h-10 rounded border border-[#c5cfda] px-3 text-sm font-medium text-[#25313d]"
    >
      Attach file
    </HydrationSafeButton>
  );
}
