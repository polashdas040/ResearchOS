import React from "react";
import type { ChatMessage } from "./workspace-data";

type StreamingMessageProps = {
  message: ChatMessage;
};

export function StreamingMessage({ message }: StreamingMessageProps) {
  const messageClass =
    message.tone === "user"
      ? "border-[#d7dde6] bg-[#f8fafc]"
      : message.tone === "assistant"
        ? "border-[#bfd8ce] bg-[#f4fbf7]"
        : "border-[#e0d2aa] bg-[#fff9ea]";

  return (
    <article className={message.tone === "user" ? "max-w-3xl" : "ml-auto max-w-3xl"}>
      <p className="mb-2 text-xs font-medium text-[#667386]">{message.author}</p>
      <div className={`rounded border p-4 text-sm leading-6 ${messageClass}`}>{message.content}</div>
    </article>
  );
}
