import React from "react";
import { runSteps } from "./workspace-data";

export function ResearchRunPanel() {
  return (
    <section aria-label="Research run">
      <h2 className="text-sm font-semibold">Research Run</h2>
      <ol className="mt-3 space-y-2">
        {runSteps.map((step) => (
          <li key={step.label} className="flex items-center gap-2 text-sm">
            <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${statusClass(step.status)}`} />
            <span className={step.status === "queued" ? "text-[#667386]" : ""}>{step.label}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

function statusClass(status: "complete" | "running" | "queued") {
  if (status === "complete") {
    return "bg-emerald-500";
  }
  if (status === "running") {
    return "bg-amber-500";
  }
  return "bg-[#b5bfca]";
}
