import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { expect, it, vi } from "vitest";
import { MessageComposer } from "./MessageComposer";

it("shows attached files as clickable chips above the message input", () => {
  const onOpenFile = vi.fn(async () => undefined);
  render(
    <MessageComposer
      onSubmit={vi.fn()}
      onOpenFile={onOpenFile}
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

  expect(screen.getByRole("button", { name: "paper.pdf READY" })).toBeInTheDocument();
});

it("opens attached file chips through the authenticated file handler", async () => {
  const onOpenFile = vi.fn(async () => undefined);
  render(
    <MessageComposer
      onSubmit={vi.fn()}
      onOpenFile={onOpenFile}
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

  fireEvent.click(screen.getByRole("button", { name: "paper.pdf READY" }));

  await waitFor(() => expect(onOpenFile).toHaveBeenCalledWith("file-1"));
});

it("can send a message while keeping attachments outside the chat transcript", async () => {
  const onSubmit = vi.fn(async () => undefined);
  render(
    <MessageComposer
      onSubmit={onSubmit}
      onOpenFile={vi.fn(async () => undefined)}
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
  expect(screen.getByRole("button", { name: "paper.pdf READY" })).toBeInTheDocument();
});
