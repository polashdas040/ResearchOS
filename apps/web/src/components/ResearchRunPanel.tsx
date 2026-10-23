import React from "react";
import { researchRun, ResearchRunState } from "./workspace-data";

type ResearchRunPanelProps = {
  run?: ResearchRunState;
  onRetry?: () => void;
  onCancel?: () => void;
};

export function ResearchRunPanel({
  run = researchRun,
  onRetry,
  onCancel
}: ResearchRunPanelProps) {
  const currentStep =
    run.steps.find((step) => step.status === "running" || step.status === "failed") ??
    run.steps.find((step) => step.status === "waiting" || step.status === "queued") ??
    run.steps[run.steps.length - 1];
  const [selectedStepLabel, setSelectedStepLabel] = React.useState<string | null>(
    currentStep?.label ?? null
  );
  const selectedStep =
    run.steps.find((step) => step.label === selectedStepLabel) ?? currentStep;

  return (
    <section aria-label="Research run">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold">Research Run</h2>
        <div className="flex gap-2">
          {run.canRetry ? (
            <button type="button" onClick={onRetry} className="text-xs font-semibold text-[#176b5b]">
              Retry
            </button>
          ) : null}
          {run.canCancel ? (
            <button type="button" onClick={onCancel} className="text-xs text-[#667386]">
              Cancel
            </button>
          ) : null}
        </div>
      </div>
      <div className="mt-3 rounded border border-[#d7dde6] bg-white p-3 text-xs">
        <p className="font-semibold text-[#536174]">Prompt</p>
        <p className="mt-1 leading-5 text-[#172026]">
          {run.prompt || "No research run started"}
        </p>
        <div className="mt-3 flex gap-4 text-[#667386]">
          <span>Started {run.startedAt || "-"}</span>
          <span>Elapsed {run.elapsed}</span>
        </div>
      </div>
      {currentStep ? (
        <div className="mt-3 rounded border border-[#c6d8d2] bg-[#f3faf7] p-3 text-xs">
          <p className="font-semibold text-[#536174]">Current agent</p>
          <p className="mt-1 text-sm font-semibold text-[#172026]">{currentStep.agent}</p>
          <p className="mt-1 text-[#536174]">
            {currentStep.label} - {statusLabel(currentStep.status)}
          </p>
        </div>
      ) : null}
      <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-[#667386]">Pipeline</p>
      <ol className="mt-2 space-y-2">
        {run.steps.map((step) => (
          <li key={step.label} className="rounded border border-[#e1e6eb] bg-white p-2.5 text-sm">
            <button
              type="button"
              onClick={() => setSelectedStepLabel(step.label)}
              className="flex w-full items-start gap-2 text-left"
              aria-pressed={selectedStep?.label === step.label}
            >
              <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${statusClass(step.status)}`} />
              <span className="min-w-0 flex-1">
                <span className="flex items-center justify-between gap-2">
                  <span className={step.status === "queued" || step.status === "waiting" ? "text-[#667386]" : ""}>
                    {step.label}
                  </span>
                  <span className="shrink-0 text-[11px] text-[#667386]">{statusLabel(step.status)}</span>
                </span>
                <span className="mt-1 block text-xs text-[#536174]">{step.agent}</span>
                <span className="mt-1 flex gap-3 text-[11px] text-[#84909d]">
                  <span>{step.startedAt ? `Started ${step.startedAt}` : "Not started"}</span>
                  {step.duration ? <span>{step.duration}</span> : null}
                </span>
                {step.detail ? <span className="mt-1 block text-xs text-[#667386]">{step.detail}</span> : null}
              </span>
            </button>
          </li>
        ))}
      </ol>
      {selectedStep ? (
        <section
          aria-label="Agent details"
          className="mt-4 rounded border border-[#d7dde6] bg-white p-3 text-xs"
        >
          <p className="font-semibold text-[#536174]">Agent</p>
          <p className="mt-1 text-sm font-semibold text-[#172026]">{selectedStep.agent}</p>
          <p className="mt-3 font-semibold text-[#536174]">Objective</p>
          <p className="mt-1 text-[#172026]">{selectedStep.label}</p>
          <p className="mt-3 font-semibold text-[#536174]">Result summary</p>
          <p className="mt-1 text-[#667386]">
            {selectedStep.detail || `${statusLabel(selectedStep.status)}; no result summary yet.`}
          </p>
        </section>
      ) : null}
      <div className="mt-4 grid grid-cols-2 gap-3 border-t border-[#d7dde6] pt-3 text-xs">
        <div>
          <p className="font-semibold text-[#536174]">Sources</p>
          <ul className="mt-1 space-y-1 text-[#667386]">
            {run.sources.map((source) => <li key={source}>{source}</li>)}
          </ul>
          <p className="mt-3 font-semibold text-[#536174]">Tools</p>
          <ul className="mt-1 space-y-1 text-[#667386]">
            {run.toolsUsed.map((tool) => <li key={tool}>{tool}</li>)}
          </ul>
        </div>
        <div>
          <p className="font-semibold text-[#536174]">Cost</p>
          <p className="mt-1 text-[#667386]">{run.cost}</p>
          <p className="mt-3 font-semibold text-[#536174]">Artifacts</p>
          <ul className="mt-1 space-y-1 text-[#176b5b]">
            {run.artifacts.map((artifact) => <li key={artifact}>{artifact}</li>)}
          </ul>
        </div>
      </div>
      {run.error ? (
        <p role="alert" className="mt-3 border-l-2 border-red-400 pl-2 text-xs text-red-700">
          {run.error}
        </p>
      ) : null}
    </section>
  );
}

function statusClass(status: "complete" | "running" | "waiting" | "queued" | "failed" | "cancelled") {
  if (status === "complete") {
    return "bg-emerald-500";
  }
  if (status === "running") {
    return "bg-amber-500";
  }
  if (status === "failed") {
    return "bg-red-500";
  }
  if (status === "cancelled") {
    return "bg-slate-400";
  }
  return "bg-[#b5bfca]";
}

function statusLabel(status: "complete" | "running" | "waiting" | "queued" | "failed" | "cancelled") {
  if (status === "complete") return "Complete";
  if (status === "running") return "Running";
  if (status === "waiting") return "Waiting";
  if (status === "failed") return "Failed";
  if (status === "cancelled") return "Cancelled";
  return "Queued";
}
