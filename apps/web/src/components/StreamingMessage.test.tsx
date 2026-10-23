import { render, screen } from "@testing-library/react";
import React from "react";
import { expect, it } from "vitest";
import { StreamingMessage } from "./StreamingMessage";

it("renders assistant markdown as formatted content instead of raw tokens", () => {
  render(
    <StreamingMessage
      message={{
        id: "assistant-1",
        author: "ResearchOS",
        tone: "assistant",
        content: "## What is RAG?\n**RAG** grounds answers.\n- Retrieves evidence\n- Generates a response\n```python\nprint('rag')\n```"
      }}
    />
  );

  expect(screen.getByRole("heading", { name: "What is RAG?" })).toBeInTheDocument();
  expect(screen.getByText("RAG", { selector: "strong" })).toBeInTheDocument();
  expect(screen.getByRole("list")).toBeInTheDocument();
  expect(screen.getByText("print('rag')")).toBeInTheDocument();
  expect(screen.queryByText(/\*\*RAG\*\*/)).not.toBeInTheDocument();
});
