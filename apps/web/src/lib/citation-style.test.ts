import { describe, expect, it } from "vitest";
import { citationMarker, formatReference } from "./citation-style";

const reference = {
  number: 2,
  file_id: "source-2",
  filename: "agent-evaluation.pdf",
  citation: '[2] A. Researcher, "Agent Evaluation," Research Journal, 2025, doi: 10.1000/agents.',
  evidence: "Verified evidence"
};

describe("citation styles", () => {
  it("formats inline citations for supported styles", () => {
    expect(citationMarker(reference, "IEEE")).toBe("[2]");
    expect(citationMarker(reference, "APA 7")).toBe("(Researcher, 2025)");
    expect(citationMarker(reference, "Harvard")).toBe("(Researcher 2025)");
    expect(citationMarker(reference, "MLA 9")).toBe("(Researcher)");
  });

  it("formats bibliography entries in the selected style", () => {
    expect(formatReference(reference, "IEEE")).toMatch(/^\[2\]/);
    expect(formatReference(reference, "APA 7")).toContain("(2025). Agent Evaluation.");
    expect(formatReference(reference, "Harvard")).toContain("(2025) 'Agent Evaluation'");
    expect(formatReference(reference, "MLA 9")).toContain("“Agent Evaluation.”");
  });
});
