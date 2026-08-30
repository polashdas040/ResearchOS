import React from "react";
import { MessageComposer } from "./MessageComposer";
import { StreamingMessage } from "./StreamingMessage";
import { messages } from "./workspace-data";

export function ChatThread() {
  return (
    <main aria-label="Research chat" className="flex min-h-[620px] flex-col bg-white">
      <div className="border-b border-[#d7dde6] px-5 py-4">
        <p className="text-xs font-medium uppercase text-[#667386]">Current run</p>
        <h1 className="mt-1 text-lg font-semibold">Biomarker evidence synthesis</h1>
        <p className="mt-1 text-sm text-[#536174]">Citation validation in progress</p>
      </div>
      <div className="flex-1 space-y-5 overflow-y-auto px-5 py-6">
        {messages.map((message) => (
          <StreamingMessage key={message.id} message={message} />
        ))}
        <section aria-label="Workspace metrics" className="grid gap-3 md:grid-cols-3">
          <Metric label="Sources" value="17" />
          <Metric label="Claims" value="24" />
          <Metric label="Warnings" value="3" emphasis />
        </section>
      </div>
      <MessageComposer />
    </main>
  );
}

type MetricProps = {
  label: string;
  value: string;
  emphasis?: boolean;
};

function Metric({ label, value, emphasis = false }: MetricProps) {
  return (
    <div className="rounded border border-[#d7dde6] bg-[#f8fafc] p-3">
      <p className="text-xs text-[#667386]">{label}</p>
      <p className={`mt-1 text-lg font-semibold ${emphasis ? "text-[#8a5b00]" : ""}`}>{value}</p>
    </div>
  );
}
