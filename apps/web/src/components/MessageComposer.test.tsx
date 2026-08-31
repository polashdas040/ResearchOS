import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { expect, it, vi } from "vitest";
import { MessageComposer } from "./MessageComposer";

it("shows attached files as clickable chips above the message input", () => {
  render(
    <MessageComposer
      onSubmit={vi.fn()}
      attachedFiles={[
        {
          id: "file-1",
          filename: "paper.pdf",
          status: "READY",
          downloadUrl: "http://localhost:8000/files/file-1/download"
        }
      ]}
    />
  );

  expect(screen.getByRole("link", { name: "paper.pdf READY" })).toHaveAttribute(
    "href",
    "http://localhost:8000/files/file-1/download"
  );
});

it("can send a message while keeping attachments outside the chat transcript", async () => {
  const onSubmit = vi.fn(async () => undefined);
  render(
    <MessageComposer
      onSubmit={onSubmit}
      attachedFiles={[
        {
          id: "file-1",
          filename: "paper.pdf",
          status: "READY",
          downloadUrl: "http://localhost:8000/files/file-1/download"
        }
      ]}
    />
  );

  fireEvent.change(screen.getByPlaceholderText("Ask ResearchOS..."), {
    target: { value: "summarize this" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Send message" }));

  await waitFor(() => expect(onSubmit).toHaveBeenCalledWith("summarize this"));
  expect(screen.getByRole("link", { name: "paper.pdf READY" })).toBeInTheDocument();
});
