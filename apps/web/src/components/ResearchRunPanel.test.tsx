import React from "react";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ResearchRunPanel } from "./ResearchRunPanel";

const run = {
  prompt: "Find evidence for longitudinal biomarker signals.",
  startedAt: "10:42:18",
  elapsed: "02m 14s",
  steps: [
    { label: "Literature search", agent: "Literature Agent", status: "complete" as const, startedAt: "10:42:18", duration: "38s" },
    { label: "Feasibility review", agent: "Feasibility Agent", status: "waiting" as const, startedAt: "10:43:02", duration: "Waiting for dataset" },
    { label: "Verification", agent: "Scientific Critic", status: "failed" as const, detail: "retry available" }
  ],
  sources: ["17 selected papers"],
  toolsUsed: ["document.search", "citation.resolve"],
  cost: "1,240 credits",
  error: "Verification needs attention.",
  artifacts: ["Evidence Map"],
  canRetry: true,
  canCancel: true
};

describe("ResearchRunPanel", () => {
  it("renders progress context and exposes retry/cancel actions", () => {
    const onRetry = vi.fn();
    const onCancel = vi.fn();
    render(<ResearchRunPanel run={run} onRetry={onRetry} onCancel={onCancel} />);

    expect(screen.getByText("Feasibility review")).toBeInTheDocument();
    expect(screen.getByText("Find evidence for longitudinal biomarker signals.")).toBeInTheDocument();
    expect(screen.getByText("Literature Agent")).toBeInTheDocument();
    expect(screen.getByText("Current agent")).toBeInTheDocument();
    expect(screen.getAllByText("Scientific Critic").length).toBeGreaterThan(0);
    expect(screen.getByText("Waiting")).toBeInTheDocument();
    expect(screen.getByText("17 selected papers")).toBeInTheDocument();
    expect(screen.getByText("document.search")).toBeInTheDocument();
    expect(screen.getByText("citation.resolve")).toBeInTheDocument();
    expect(screen.getByText("1,240 credits")).toBeInTheDocument();
    expect(screen.getByText("Evidence Map")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Verification needs attention.");

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onRetry).toHaveBeenCalledOnce();
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("opens structured agent workflow details without hidden reasoning", () => {
    render(<ResearchRunPanel run={run} />);

    fireEvent.click(screen.getByRole("button", { name: /Verification Failed/ }));

    const details = screen.getByRole("region", { name: "Agent details" });
    expect(details).toBeInTheDocument();
    expect(within(details).getByText("Agent")).toBeInTheDocument();
    expect(within(details).getByText("Scientific Critic")).toBeInTheDocument();
    expect(within(details).getByText("Result summary")).toBeInTheDocument();
    expect(within(details).getByText("retry available")).toBeInTheDocument();
    expect(screen.queryByText(/chain-of-thought/i)).not.toBeInTheDocument();
  });
});
