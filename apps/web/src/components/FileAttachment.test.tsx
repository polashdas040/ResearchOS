import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { expect, it, vi } from "vitest";
import { FileAttachment } from "./FileAttachment";

it("calls the file selection handler when a file is selected", () => {
  const onFileSelected = vi.fn(async () => undefined);
  render(<FileAttachment onFileSelected={onFileSelected} />);

  const input = screen.getByLabelText("Attach file");
  const file = new File(["hello"], "notes.txt", { type: "text/plain" });
  fireEvent.change(input, { target: { files: [file] } });

  expect(onFileSelected).toHaveBeenCalledWith(file);
});
