import React from "react";
import { HydrationSafeButton } from "./HydrationSafeControls";
import { conversations } from "./workspace-data";

export function ConversationSidebar() {
  return (
    <nav
      aria-label="Conversations"
      className="border-b border-[#d7dde6] bg-white p-4 lg:border-b-0 lg:border-r"
    >
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold">Conversations</h2>
        <HydrationSafeButton
          type="button"
          className="rounded border border-[#c5cfda] px-3 py-1.5 text-sm font-medium"
        >
          New
        </HydrationSafeButton>
      </div>
      <div className="space-y-2">
        {conversations.map((conversation) => (
          <HydrationSafeButton
            key={conversation.id}
            type="button"
            className={`w-full rounded border px-3 py-3 text-left ${
              conversation.active
                ? "border-[#96b5aa] bg-[#f1f8f5]"
                : "border-transparent hover:border-[#c5cfda] hover:bg-[#f7f9fb]"
            }`}
          >
            <span className="block truncate text-sm font-medium">{conversation.title}</span>
            <span className="mt-1 block text-xs text-[#667386]">{conversation.updatedAt}</span>
          </HydrationSafeButton>
        ))}
      </div>
    </nav>
  );
}
