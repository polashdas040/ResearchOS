import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import React from "react";
import { beforeEach, expect, it, vi } from "vitest";
import { WorkspaceShell } from "./WorkspaceShell";
import * as apiClient from "../lib/api-client";

vi.mock("../lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("../lib/api-client")>("../lib/api-client");
  return {
    ...actual,
    createConversation: vi.fn(),
    getConversation: vi.fn(),
    getStoredAccessToken: vi.fn(),
    listProjectFileReferences: vi.fn(),
    deleteProjectFile: vi.fn(),
    saveLiteratureReference: vi.fn(),
    searchLiteratureReferences: vi.fn(),
    listProjectFiles: vi.fn(),
    listProjects: vi.fn(),
    listConversations: vi.fn(),
    openProjectFile: vi.fn(),
    streamChatMessage: vi.fn(),
    uploadProjectFile: vi.fn()
  };
});

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
  vi.mocked(apiClient.getStoredAccessToken).mockReturnValue("token");
  vi.mocked(apiClient.listProjects).mockResolvedValue({
    items: [{ id: "project-1", name: "Project", description: null }]
  });
  vi.mocked(apiClient.listProjectFiles).mockResolvedValue({ items: [], total: 0 });
  vi.mocked(apiClient.listProjectFileReferences).mockResolvedValue({ items: [] });
  vi.mocked(apiClient.saveLiteratureReference).mockResolvedValue({
    id: "saved-source-1",
    filename: "Verified_Research_Paper_summary.txt",
    content_type: "text/plain",
    status: "READY"
  });
  vi.mocked(apiClient.searchLiteratureReferences).mockResolvedValue({
    items: [{
      number: 1,
      source_id: "https://openalex.org/W1",
      title: "Verified Research Paper",
      citation: '[1] A. Researcher, "Verified Research Paper," Research Journal, 2025.',
      evidence: "The study reports evidence relevant to the generated claim.",
      url: "https://doi.org/10.1000/verified"
    }]
  });
  vi.mocked(apiClient.listConversations).mockResolvedValue({
    items: [{ id: "conversation-1", project_id: "project-1", title: "Conversation" }]
  });
  vi.mocked(apiClient.getConversation).mockResolvedValue({
    id: "conversation-1",
    project_id: "project-1",
    title: "Conversation",
    messages: { items: [] }
  });
  vi.mocked(apiClient.streamChatMessage).mockImplementation(async (_conversationId, _content, onDelta) => {
    onDelta("ResearchOS received the attached file.");
  });
  vi.mocked(apiClient.uploadProjectFile).mockResolvedValue({
    id: "file-1",
    filename: "paper.pdf",
    status: "READY"
  });
});

function disableAutocomplete() {
  const control = screen.getByRole("switch", { name: "Autocomplete" });
  if (control.getAttribute("aria-checked") === "true") fireEvent.click(control);
}

it("uses an attachment-only setup without exposing it as an AI chat turn", async () => {
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());

  const input = screen.getByLabelText("Import PDF document");
  fireEvent.change(input, {
    target: {
      files: [new File(["pdf"], "paper.pdf", { type: "application/pdf" })]
    }
  });

  await waitFor(() => expect(apiClient.uploadProjectFile).toHaveBeenCalledWith("project-1", expect.any(File)));
  expect(screen.getByLabelText("Document prompt")).toHaveValue(
    'Analyze the imported PDF "paper" and create an evidence-grounded research document that preserves its key findings, methods, limitations, and references.'
  );
  await waitFor(() => expect(screen.getByRole("button", { name: "paper.pdf READY" })).toBeInTheDocument());
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));

  await waitFor(() => expect(screen.getByRole("toolbar", { name: "Editor toolbar" })).toBeInTheDocument());
  expect(apiClient.streamChatMessage).not.toHaveBeenCalled();
  expect(screen.queryByText("ResearchOS received the attached file.")).not.toBeInTheDocument();
  expect(screen.queryByRole("complementary", { name: "Research assistant" })).not.toBeInTheDocument();
});

it("opens an attached source from the document editor", async () => {
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "Analyze the attached research paper" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Generate Introduction" })).toBeInTheDocument());

  const input = screen.getAllByLabelText("Attach file").find((element) => element instanceof HTMLInputElement);
  if (!(input instanceof HTMLInputElement)) {
    throw new Error("File input was not rendered.");
  }
  fireEvent.change(input, {
    target: {
      files: [new File(["pdf"], "paper.pdf", { type: "application/pdf" })]
    }
  });

  const sourceButton = await screen.findByRole("button", { name: "Open paper.pdf" });
  expect(screen.getByText("Ready and included in project-source context")).toBeInTheDocument();
  fireEvent.click(sourceButton);
  expect(apiClient.openProjectFile).toHaveBeenCalledWith("file-1");
});

it("expands verified sources and opens a source file", async () => {
  vi.mocked(apiClient.listProjectFiles).mockResolvedValue({
    items: [{ id: "source-1", filename: "agent-study.pdf", content_type: "application/pdf", status: "READY" }],
    total: 1
  });
  vi.mocked(apiClient.listProjectFileReferences).mockResolvedValue({
    items: [{
      number: 1,
      file_id: "source-1",
      filename: "agent-study.pdf",
      citation: '[1] A. Researcher, "Agent Evaluation," Research Journal, 2025.'
    }]
  });

  render(<WorkspaceShell projectId="project-1" />);
  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "Evaluate autonomous research agents" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "1 verified source available" })).toBeInTheDocument());

  const referencesSection = screen.getByRole("region", { name: "References section" });
  expect(referencesSection).toHaveTextContent("Verified citations used in generated sections will appear here.");
  expect(referencesSection).not.toHaveTextContent("Agent Evaluation");

  fireEvent.click(screen.getByRole("button", { name: "1 verified source available" }));

  const sources = screen.getByRole("list", { name: "Available sources" });
  expect(within(sources).getByText(/Agent Evaluation/)).toBeInTheDocument();
  fireEvent.click(within(sources).getByRole("button", { name: "Open file" }));
  expect(apiClient.openProjectFile).toHaveBeenCalledWith("source-1");
});

it("opens project navigation views and searches scholarly papers", async () => {
  vi.mocked(apiClient.listProjectFiles).mockResolvedValue({
    items: [{ id: "source-1", filename: "paper.pdf", content_type: "application/pdf", status: "READY" }],
    total: 1
  });
  vi.mocked(apiClient.listProjectFileReferences).mockResolvedValue({
    items: [{
      number: 1,
      file_id: "source-1",
      filename: "paper.pdf",
      citation: '[1] A. Researcher, "Verified Research Paper," Research Journal, 2025.'
    }]
  });
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  expect(screen.queryByRole("button", { name: "Documents" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Library" }));
  const library = await screen.findByRole("main", { name: "Library workspace" });
  expect(within(library).getByText("paper.pdf")).toBeInTheDocument();
  fireEvent.click(within(library).getByRole("button", { name: "Open" }));
  expect(apiClient.openProjectFile).toHaveBeenCalledWith("source-1");
  vi.spyOn(window, "confirm").mockReturnValue(true);
  fireEvent.click(within(library).getByRole("button", { name: "Delete" }));
  await waitFor(() => expect(apiClient.deleteProjectFile).toHaveBeenCalledWith("source-1"));
  expect(within(library).queryByText("paper.pdf")).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Find papers" }));
  const papers = await screen.findByRole("main", { name: "Find papers workspace" });
  fireEvent.change(within(papers).getByLabelText("Paper search query"), {
    target: { value: "retrieval augmented generation" }
  });
  fireEvent.click(within(papers).getByRole("button", { name: "Search" }));

  await waitFor(() => expect(apiClient.searchLiteratureReferences).toHaveBeenCalledWith(
    "project-1",
    "retrieval augmented generation",
    5
  ));
  expect(await within(papers).findByText("Verified Research Paper")).toBeInTheDocument();
  fireEvent.click(within(papers).getByRole("button", { name: "Save summary to Library" }));
  await waitFor(() => expect(apiClient.saveLiteratureReference).toHaveBeenCalled());
  expect(await within(papers).findByRole("button", { name: "Saved to Library" })).toBeDisabled();
});

it("keeps uploaded PDFs visible on the sent message and reuses them for follow-up questions", async () => {
  vi.mocked(apiClient.listProjectFileReferences).mockResolvedValue({
    items: [{
      number: 1,
      file_id: "file-1",
      filename: "paper.pdf",
      citation: '[1] A. Researcher, "Uploaded Paper," Research Journal, 2025.'
    }]
  });
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());

  const input = document.querySelector('input[type="file"]');
  if (!(input instanceof HTMLInputElement)) {
    throw new Error("File input was not rendered.");
  }
  fireEvent.change(input, {
    target: {
      files: [new File(["pdf"], "paper.pdf", { type: "application/pdf" })]
    }
  });
  await waitFor(() => expect(screen.getByRole("button", { name: "paper.pdf READY" })).toBeInTheDocument());

  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "according to the pdf file pls tell me about the result" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));

  await waitFor(() => expect(screen.getByRole("toolbar", { name: "Editor toolbar" })).toBeInTheDocument());
  expect(apiClient.streamChatMessage).not.toHaveBeenCalled();

  fireEvent.click(within(screen.getByRole("main", { name: "Research chat" })).getByRole("button", { name: "AI Chat" }));
  fireEvent.change(screen.getByPlaceholderText("Ask ResearchOS..."), {
    target: { value: "tell me about the uploaded pdf result?" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Send message" }));

  await waitFor(() => expect(apiClient.streamChatMessage).toHaveBeenCalledTimes(1));
  expect(apiClient.streamChatMessage).toHaveBeenLastCalledWith(
    "conversation-1",
    "tell me about the uploaded pdf result?",
    expect.any(Function),
    ["file-1"],
    expect.objectContaining({
      requireReferences: true,
      citationStyle: "IEEE",
      referenceContext: expect.stringContaining("Uploaded Paper")
    })
  );
  expect(apiClient.searchLiteratureReferences).not.toHaveBeenCalled();
});

it("opens the academic editor and compact agent chat after the first prompt", async () => {
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());

  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "tell me about what is RAG?" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));

  await waitFor(() => expect(screen.getByText("Section prompts")).toBeInTheDocument());
  expect(screen.getByLabelText("Document title")).toHaveTextContent(
    "Retrieval-Augmented Generation: Principles, Architecture, and Applications"
  );
  expect(screen.getByRole("toolbar", { name: "Editor toolbar" })).toBeInTheDocument();
  const documentCanvas = screen.getByLabelText("Document canvas");
  expect(documentCanvas).toHaveClass("lg:overflow-y-auto");
  expect(screen.getByLabelText("Font family")).toHaveValue("Times New Roman");
  expect(screen.getByLabelText("Font size")).toHaveValue("10");
  expect(documentCanvas.querySelector("article")).toHaveStyle({ fontFamily: "Times New Roman", fontSize: "10pt" });
  expect(screen.queryByRole("button", { name: "Code" })).not.toBeInTheDocument();
  expect(screen.getAllByText("Introduction").length).toBeGreaterThan(0);
  expect(screen.getAllByText("Literature Review").length).toBeGreaterThan(0);
  expect(screen.getAllByText("Methodology").length).toBeGreaterThan(0);
  expect(screen.getAllByText("Results").length).toBeGreaterThan(0);
  expect(screen.getAllByText("Discussion").length).toBeGreaterThan(0);
  expect(screen.getAllByText("Conclusion").length).toBeGreaterThan(0);
  expect(screen.getByRole("button", { name: "Configure context" })).toBeInTheDocument();
  const introduction = screen.getByRole("region", { name: "Introduction section" });
  const title = screen.getByLabelText("Document title");
  title.textContent = "Editable research title";
  fireEvent.blur(title);
  expect(screen.getByLabelText("Document title")).toHaveTextContent("Editable research title");
  let introductionEditor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  introductionEditor.textContent = "A manually written introduction.";
  fireEvent.blur(introductionEditor);
  introductionEditor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  expect(introductionEditor).toHaveTextContent("A manually written introduction.");
  const editableText = introductionEditor.querySelector("p")?.firstChild;
  expect(editableText).toBeTruthy();
  const range = document.createRange();
  range.setStart(editableText!, 2);
  range.setEnd(editableText!, 10);
  window.getSelection()?.removeAllRanges();
  window.getSelection()?.addRange(range);
  fireEvent.mouseDown(screen.getByRole("button", { name: "Bold" }));
  expect(await within(introduction).findByText("manually", { selector: "strong" })).toBeInTheDocument();
  introductionEditor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  const boldText = within(introduction).getByText("manually", { selector: "strong" }).firstChild;
  const boldRange = document.createRange();
  boldRange.selectNodeContents(boldText!);
  window.getSelection()?.removeAllRanges();
  window.getSelection()?.addRange(boldRange);
  fireEvent.mouseDown(screen.getByRole("button", { name: "Bold" }));
  await waitFor(() => expect(within(introduction).queryByText("manually", { selector: "strong" })).not.toBeInTheDocument());

  introductionEditor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  const plainText = introductionEditor.querySelector("p")?.firstChild;
  const styledRange = document.createRange();
  styledRange.setStart(plainText!, 2);
  styledRange.setEnd(plainText!, 10);
  window.getSelection()?.removeAllRanges();
  window.getSelection()?.addRange(styledRange);
  fireEvent.change(screen.getByLabelText("Font family"), { target: { value: "Garamond" } });
  const styledWord = await within(introduction).findByText("manually", { selector: "span" });
  expect(styledWord).toHaveStyle({ fontFamily: "Garamond" });
  expect(documentCanvas.querySelector("article")).toHaveStyle({ fontFamily: "Times New Roman", fontSize: "10pt" });

  const sizeRange = document.createRange();
  sizeRange.selectNodeContents(styledWord.firstChild!);
  window.getSelection()?.removeAllRanges();
  window.getSelection()?.addRange(sizeRange);
  fireEvent.change(screen.getByLabelText("Font size"), { target: { value: "12" } });
  const resizedWord = await within(introduction).findByText("manually", { selector: "span" });
  expect(resizedWord).toHaveStyle({ fontFamily: "Garamond", fontSize: "12pt" });

  introductionEditor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  const endRange = document.createRange();
  endRange.selectNodeContents(introductionEditor);
  endRange.collapse(false);
  window.getSelection()?.removeAllRanges();
  window.getSelection()?.addRange(endRange);
  fireEvent.mouseUp(introductionEditor);
  fireEvent.mouseDown(screen.getByRole("button", { name: "Equation" }));
  const equationDialog = screen.getByRole("dialog", { name: "Insert equation" });
  fireEvent.change(within(equationDialog).getByLabelText("Equation"), { target: { value: "E = mc^2" } });
  fireEvent.click(within(equationDialog).getByRole("button", { name: "Insert equation" }));
  expect(await within(introduction).findByLabelText("Equation")).toHaveTextContent("E = mc^2");

  introductionEditor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  const imageRange = document.createRange();
  imageRange.selectNodeContents(introductionEditor);
  imageRange.collapse(false);
  window.getSelection()?.removeAllRanges();
  window.getSelection()?.addRange(imageRange);
  fireEvent.mouseUp(introductionEditor);
  const imageReader = vi.spyOn(FileReader.prototype, "readAsDataURL").mockImplementation(function (this: FileReader) {
    Object.defineProperty(this, "result", { configurable: true, value: "data:image/png;base64,aW1hZ2U=" });
    this.onload?.call(this, new ProgressEvent("load") as ProgressEvent<FileReader>);
  });
  fireEvent.change(screen.getByLabelText("Insert image from device"), {
    target: { files: [new File(["image"], "study-figure.png", { type: "image/png" })] }
  });
  const insertedImage = await within(introduction).findByRole("img", { name: "study-figure" });
  expect(insertedImage).toBeInTheDocument();
  imageReader.mockRestore();
  fireEvent.click(insertedImage);
  const imageAlignment = screen.getByRole("toolbar", { name: "Image alignment" });
  expect(within(imageAlignment).getByRole("button", { name: "Align image left" })).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(within(imageAlignment).getByRole("button", { name: "Align image center" }));
  const centeredImage = await within(introduction).findByRole("img", { name: "study-figure" });
  expect(centeredImage.parentElement).toHaveAttribute("data-image-align", "center");
  expect(centeredImage.parentElement).toHaveClass("justify-center");

  expect(screen.queryByRole("button", { name: "Share" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Export" }));
  const exportDialog = screen.getByRole("dialog", { name: "Export draft" });
  expect(within(exportDialog).getByRole("button", { name: /Word document/ })).toBeInTheDocument();
  expect(within(exportDialog).getByRole("button", { name: /PDF document/ })).toBeInTheDocument();
  fireEvent.click(within(exportDialog).getByRole("button", { name: "Close" }));

  fireEvent.click(screen.getByRole("button", { name: "Review" }));
  const reviewDialog = screen.getByRole("dialog", { name: "Document review" });
  expect(within(reviewDialog).getByText("Words")).toBeInTheDocument();
  expect(within(reviewDialog).getByText("Citations")).toBeInTheDocument();
  expect(within(reviewDialog).getByText("Completed")).toBeInTheDocument();
  expect(within(reviewDialog).getByText("Sections")).toBeInTheDocument();
  expect(within(reviewDialog).getByText("Empty sections: Literature Review, Methodology, Results, Discussion, Conclusion.")).toBeInTheDocument();
  fireEvent.click(within(reviewDialog).getByRole("button", { name: "Close" }));

  const autocomplete = screen.getByRole("switch", { name: "Autocomplete" });
  expect(autocomplete).toHaveAttribute("aria-checked", "true");
  fireEvent.click(autocomplete);
  expect(autocomplete).toHaveAttribute("aria-checked", "false");

  expect(screen.getByLabelText("Introduction heading")).toHaveAttribute("contenteditable", "true");
  expect(screen.queryByRole("region", { name: "AI conversation" })).not.toBeInTheDocument();
  expect(screen.queryByRole("complementary", { name: "Research assistant" })).not.toBeInTheDocument();
  fireEvent.click(within(screen.getByRole("main", { name: "Research chat" })).getByRole("button", { name: "AI Chat" }));
  expect(screen.getByRole("complementary", { name: "Research assistant" })).toBeInTheDocument();
  expect(within(screen.getByLabelText("Current agent")).getByText("Academic Writing Agent")).toBeInTheDocument();
  expect(screen.queryByText("Research pipeline")).not.toBeInTheDocument();
  expect(screen.getByLabelText("Chat history")).toHaveClass("overflow-y-auto");
  expect(screen.getByRole("region", { name: "References section" })).toBeInTheDocument();
});

it("inserts a sized table and edits its selected row and column", async () => {
  render(<WorkspaceShell projectId="project-1" />);
  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());

  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "Editable research tables" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Generate Introduction" })).toBeInTheDocument());

  const introduction = screen.getByRole("region", { name: "Introduction section" });
  let introductionEditor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  introductionEditor.innerHTML = "<p>Generate complex and context-aware <strong>interactions</strong>.</p>";
  const formattedText = introductionEditor.querySelector("strong")?.firstChild;
  expect(formattedText).toBeTruthy();
  const insertionRange = document.createRange();
  insertionRange.setStart(formattedText!, formattedText!.textContent?.length ?? 0);
  insertionRange.collapse(true);
  window.getSelection()?.removeAllRanges();
  window.getSelection()?.addRange(insertionRange);

  fireEvent.click(screen.getByRole("button", { name: "Table" }));
  const dialog = screen.getByRole("dialog", { name: "Insert table" });
  fireEvent.change(within(dialog).getByLabelText("Table rows"), { target: { value: "2" } });
  fireEvent.change(within(dialog).getByLabelText("Table columns"), { target: { value: "3" } });
  fireEvent.click(within(dialog).getByRole("button", { name: "Insert table" }));

  let table = await within(introduction).findByRole("table");
  expect(within(table).getAllByRole("row")).toHaveLength(2);
  expect(within(table).getAllByRole("columnheader")).toHaveLength(3);
  expect(within(introduction).getByText("interactions", { selector: "strong" })).toBeInTheDocument();
  introductionEditor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  expect(introductionEditor).not.toHaveTextContent("| Column 1 | Column 2 | Column 3 |");
  const trailingParagraph = introductionEditor.querySelector<HTMLElement>("[data-table-trailing-paragraph='true']");
  expect(trailingParagraph).toBeInTheDocument();
  trailingParagraph!.textContent = "Text written below the table.";
  fireEvent.input(introductionEditor);
  fireEvent.blur(introductionEditor);
  await waitFor(() => expect(within(introduction).getAllByText("Text written below the table.")).toHaveLength(1));

  table = within(introduction).getByRole("table");
  fireEvent.click(within(table).getAllByRole("cell")[0]);
  const tableTools = screen.getByRole("toolbar", { name: "Table tools" });
  fireEvent.click(within(tableTools).getByRole("button", { name: "Insert row below" }));
  await waitFor(() => expect(within(within(introduction).getByRole("table")).getAllByRole("row")).toHaveLength(3));
  table = within(introduction).getByRole("table");

  fireEvent.click(within(table).getAllByRole("cell")[0]);
  fireEvent.click(within(screen.getByRole("toolbar", { name: "Table tools" })).getByRole("button", { name: "Delete column" }));
  await waitFor(() => expect(within(within(introduction).getByRole("table")).getAllByRole("columnheader")).toHaveLength(2));
  table = within(introduction).getByRole("table");

  fireEvent.click(within(table).getAllByRole("cell")[0]);
  fireEvent.click(within(screen.getByRole("toolbar", { name: "Table tools" })).getByRole("button", { name: "Delete table" }));
  await waitFor(() => expect(within(introduction).queryByRole("table")).not.toBeInTheDocument());

  introductionEditor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  introductionEditor.textContent = "Existing text | Column 1 | Column 2 | | --- | --- | | New cell | New cell |";
  fireEvent.input(introductionEditor);
  fireEvent.blur(introductionEditor);
  await waitFor(() => expect(within(introduction).getByRole("table")).toBeInTheDocument());
  expect(within(introduction).getByText("Existing text")).toBeInTheDocument();
}, 15_000);

it("shows recent chat messages first and loads older messages on request", async () => {
  vi.mocked(apiClient.getConversation).mockResolvedValue({
    id: "conversation-1",
    project_id: "project-1",
    title: "Conversation",
    messages: {
      items: Array.from({ length: 10 }, (_, index) => ({
        id: `message-${index + 1}`,
        message_type: index % 2 === 0 ? "USER" as const : "ASSISTANT" as const,
        content: `Chat message ${index + 1}`
      }))
    }
  });

  render(<WorkspaceShell projectId="project-1" />);
  await waitFor(() => expect(screen.getByRole("toolbar", { name: "Editor toolbar" })).toBeInTheDocument());

  fireEvent.click(within(screen.getByRole("main", { name: "Research chat" })).getByRole("button", { name: "AI Chat" }));

  expect(screen.queryByText("Chat message 3")).not.toBeInTheDocument();
  expect(screen.getByText("Chat message 10")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Load previous (2)" }));
  expect(screen.getByText("Chat message 3")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /Load previous/ })).not.toBeInTheDocument();
});

it("edits and resubmits a prompt with the selected citation style and verified sources", async () => {
  vi.mocked(apiClient.getConversation).mockResolvedValue({
    id: "conversation-1",
    project_id: "project-1",
    title: "Conversation",
    messages: { items: [
      { id: "setup-user", message_type: "USER", content: "AI agent evaluation" },
      { id: "setup-assistant", message_type: "ASSISTANT", content: "Document ready" },
      { id: "prompt-1", message_type: "USER", content: "Explain AI agents" },
      { id: "answer-1", message_type: "ASSISTANT", content: "Old answer" }
    ] }
  });
  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_id, _content, onDelta) => {
    onDelta("Revised cited answer (Researcher, 2025).\n\nReferences\nResearcher (2025). Verified Research Paper.");
  });

  render(<WorkspaceShell projectId="project-1" />);
  await waitFor(() => expect(screen.getByRole("toolbar", { name: "Editor toolbar" })).toBeInTheDocument());
  fireEvent.click(within(screen.getByRole("main", { name: "Research chat" })).getByRole("button", { name: "AI Chat" }));
  fireEvent.change(screen.getByLabelText("Chat citation style"), { target: { value: "APA 7" } });
  fireEvent.click(screen.getByRole("button", { name: "Edit prompt" }));
  fireEvent.change(screen.getByLabelText("Edit prompt"), { target: { value: "Explain AI agent evaluation" } });
  fireEvent.click(screen.getByRole("button", { name: "Submit edit" }));

  await waitFor(() => expect(apiClient.streamChatMessage).toHaveBeenCalledTimes(1));
  expect(apiClient.streamChatMessage).toHaveBeenLastCalledWith(
    "conversation-1",
    "Explain AI agent evaluation",
    expect.any(Function),
    [],
    expect.objectContaining({
      citationStyle: "APA 7",
      requireReferences: true,
      referenceContext: expect.stringContaining("Verified Research Paper")
    })
  );
  expect(screen.queryByText("Old answer")).not.toBeInTheDocument();
  expect(await screen.findByText(/Revised cited answer/)).toBeInTheDocument();
});

it("configures section context and generates content inside the document", async () => {
  vi.mocked(apiClient.listProjectFiles).mockResolvedValue({
    items: [{ id: "source-1", filename: "paper.pdf", status: "READY" }],
    total: 1
  });
  vi.mocked(apiClient.listProjectFileReferences).mockResolvedValue({
    items: [{
      number: 1,
      file_id: "source-1",
      filename: "paper.pdf",
      citation: '[1] A. Researcher, "RAG Study," unpublished manuscript, 2025.'
    }]
  });
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "tell me about what is RAG?" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));

  await waitFor(() => expect(screen.getByRole("button", { name: "Configure context" })).toBeInTheDocument());
  disableAutocomplete();
  fireEvent.click(screen.getByRole("button", { name: "Configure context" }));
  expect(screen.getByRole("dialog", { name: "Section context configuration" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("checkbox", { name: "Search scholarly sources" }));
  fireEvent.click(screen.getByRole("button", { name: "Save context" }));
  expect(screen.queryByRole("dialog", { name: "Section context configuration" })).not.toBeInTheDocument();

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_conversationId, _content, onDelta) => {
    onDelta("**RAG** ");
    onDelta("combines retrieval with generation [1].");
  });
  fireEvent.click(screen.getByRole("button", { name: "Generate Introduction" }));

  await waitFor(() =>
    expect(apiClient.streamChatMessage).toHaveBeenLastCalledWith(
      "conversation-1",
      expect.stringContaining("Write the next sentence of the Introduction section"),
      expect.any(Function),
      ["source-1"],
      expect.objectContaining({ requireReferences: false, citationStyle: "IEEE" })
    )
  );
  const introduction = screen.getByRole("region", { name: "Introduction section" });
  const firstSuggestion = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });
  expect(within(firstSuggestion).getByText(/combines retrieval with generation/)).toBeInTheDocument();
  fireEvent.click(within(firstSuggestion).getByRole("button", { name: "Accept" }));
  expect(await within(introduction).findByText("RAG", { selector: "strong" })).toBeInTheDocument();
  expect(within(introduction).getByText(/combines retrieval with generation/)).toBeInTheDocument();
  expect(within(introduction).getByText(/\[1\]/)).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "References section" })).toHaveTextContent(
    '[1] A. Researcher, "RAG Study," unpublished manuscript, 2025.'
  );
  const introductionEditor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  introductionEditor.textContent = "The researcher rewrote the introduction [1].";
  fireEvent.input(introductionEditor);
  const introductionRequest = vi.mocked(apiClient.streamChatMessage).mock.calls.at(-1)?.[1] ?? "";
  expect(introductionRequest).toContain("IEEE numbered citations");
  expect(introductionRequest).toContain("exactly one complete sentence");

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_conversationId, _content, onDelta) => {
    onDelta("It grounds generated claims in retrieved evidence [1]. This extra sentence must be discarded.");
  });
  fireEvent.click(within(introduction).getByRole("button", { name: "Continue Introduction" }));

  await waitFor(() => expect(apiClient.streamChatMessage).toHaveBeenCalledTimes(2));
  const secondSuggestion = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });
  fireEvent.click(within(secondSuggestion).getByRole("button", { name: "Accept" }));
  expect(within(introduction).getByText(/grounds generated claims in retrieved evidence/)).toBeInTheDocument();
  expect(within(introduction).queryByText(/extra sentence must be discarded/)).not.toBeInTheDocument();
  const continuationRequest = vi.mocked(apiClient.streamChatMessage).mock.calls.at(-1)?.[1] ?? "";
  expect(continuationRequest).toContain("The researcher rewrote the introduction [1].");
  expect(continuationRequest).not.toContain("**RAG** combines retrieval with generation [1].");
  expect(continuationRequest).toContain(
    "NEXT RHETORICAL MOVE: Explain why the problem matters and what consequences remain unresolved."
  );

  const updatedIntroductionEditor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  updatedIntroductionEditor.textContent = "Only the final edited introduction remains [1].";
  fireEvent.input(updatedIntroductionEditor);

  fireEvent.click(screen.getByRole("button", { name: "Literature Review" }));
  const literaturePrompt = screen.getByLabelText("Literature Review prompt");
  fireEvent.change(literaturePrompt, { target: { value: "Compare foundational and recent RAG studies." } });
  expect(literaturePrompt).toHaveValue("Compare foundational and recent RAG studies.");
  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_conversationId, _content, onDelta) => {
    onDelta("Prior work builds on the introduction [1, p. 4].");
  });
  fireEvent.click(screen.getByRole("button", { name: "Generate Literature Review" }));

  await waitFor(() => expect(apiClient.streamChatMessage).toHaveBeenCalledTimes(3));
  const literatureRequest = vi.mocked(apiClient.streamChatMessage).mock.calls.at(-1)?.[1] ?? "";
  expect(literatureRequest).toContain("Compare foundational and recent RAG studies.");
  expect(literatureRequest).toContain("EXISTING DOCUMENT");
  expect(literatureRequest).toContain("Only the final edited introduction remains [1].");
  expect(literatureRequest).not.toContain("grounds generated claims in retrieved evidence");
});

it("keeps a trailing model citation and lists its IEEE reference after acceptance", async () => {
  vi.mocked(apiClient.listProjectFiles).mockResolvedValue({
    items: [{ id: "source-1", filename: "paper.pdf", status: "READY" }],
    total: 1
  });
  vi.mocked(apiClient.listProjectFileReferences).mockResolvedValue({
    items: [{
      number: 1,
      file_id: "source-1",
      filename: "paper.pdf",
      citation: '[1] A. Researcher, "Agent Evaluation," unpublished manuscript, 2025.'
    }]
  });
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "AI agent evaluation" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Generate Introduction" })).toBeInTheDocument());
  disableAutocomplete();

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_id, _content, onDelta) => {
    onDelta("Dynamic benchmarks measure adaptation under environmental change. [1, p. 7]");
  });
  fireEvent.click(screen.getByRole("button", { name: "Generate Introduction" }));

  const introduction = screen.getByRole("region", { name: "Introduction section" });
  const suggestion = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });
  expect(suggestion).toHaveTextContent("Dynamic benchmarks measure adaptation under environmental change [1].");
  expect(screen.getByRole("region", { name: "References section" })).toHaveTextContent(
    "Verified citations used in generated sections will appear here."
  );
  fireEvent.click(within(suggestion).getByRole("button", { name: "Accept" }));

  expect(screen.getByRole("region", { name: "References section" })).toHaveTextContent(
    '[1] A. Researcher, "Agent Evaluation," unpublished manuscript, 2025.'
  );

  const editor = within(introduction).getByRole("textbox", { name: "Introduction content" });
  editor.textContent = "Dynamic benchmarks measure adaptation under environmental change.";
  fireEvent.input(editor);
  await waitFor(() => expect(screen.getByRole("region", { name: "References section" })).not.toHaveTextContent(
    "Agent Evaluation"
  ));
});

it("lists an author-date source in References when that citation style is selected", async () => {
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "Evidence-grounded AI agent evaluation" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Generate Introduction" })).toBeInTheDocument());
  disableAutocomplete();
  fireEvent.change(screen.getByLabelText("Citation style"), { target: { value: "APA 7" } });

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_id, _content, onDelta) => {
    onDelta("Dynamic evaluations expose failures under environmental change (Researcher, 2025).");
  });
  fireEvent.click(screen.getByRole("button", { name: "Generate Introduction" }));

  const introduction = screen.getByRole("region", { name: "Introduction section" });
  const suggestion = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });
  expect(suggestion).toHaveTextContent("(Researcher, 2025)");
  expect(screen.getByRole("region", { name: "References section" })).not.toHaveTextContent(
    "Verified Research Paper"
  );
  fireEvent.click(within(suggestion).getByRole("button", { name: "Accept" }));
  expect(screen.getByRole("region", { name: "References section" })).toHaveTextContent(
    "A. Researcher (2025). Verified Research Paper. Research Journal."
  );
});

it("numbers references by first manuscript appearance instead of search-result position", async () => {
  const searchItems = Array.from({ length: 15 }, (_, index) => ({
    number: index + 1,
    source_id: `https://openalex.org/W${index + 1}`,
    title: `Verified Paper ${index + 1}`,
    citation: `[${index + 1}] A. Researcher, "Verified Paper ${index + 1}," Research Journal, 2025.`,
    evidence: `Distinct supporting evidence from paper ${index + 1}.`,
    url: `https://doi.org/10.1000/verified-${index + 1}`
  }));
  vi.mocked(apiClient.searchLiteratureReferences)
    .mockResolvedValueOnce({ items: searchItems })
    .mockResolvedValueOnce({ items: [searchItems[8], ...searchItems.filter((_, index) => index !== 8)] });
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "Sequential IEEE citations" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Generate Introduction" })).toBeInTheDocument());
  disableAutocomplete();

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_id, _content, onDelta) => {
    onDelta("The first claim is supported by the leading study [1].");
  });
  fireEvent.click(screen.getByRole("button", { name: "Generate Introduction" }));
  const introduction = screen.getByRole("region", { name: "Introduction section" });
  const firstSuggestion = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });
  fireEvent.click(within(firstSuggestion).getByRole("button", { name: "Accept" }));

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_id, _content, onDelta) => {
    onDelta("A separate study establishes an additional consequence for the research design [9].");
  });
  fireEvent.click(within(introduction).getByRole("button", { name: "Continue Introduction" }));

  const secondSuggestion = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });
  expect(secondSuggestion).toHaveTextContent("research design [2].");
  expect(secondSuggestion).not.toHaveTextContent("[9]");
  fireEvent.click(within(secondSuggestion).getByRole("button", { name: "Accept" }));
  const bibliography = screen.getByRole("region", { name: "References section" });
  expect(bibliography).toHaveTextContent('[1] A. Researcher, "Verified Paper 1,"');
  expect(bibliography).toHaveTextContent('[2] A. Researcher, "Verified Paper 9,"');
});

it("retries an uncited claim instead of assigning the first reference automatically", async () => {
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "Evidence-grounded AI agents" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Generate Introduction" })).toBeInTheDocument());
  disableAutocomplete();

  vi.mocked(apiClient.streamChatMessage)
    .mockImplementationOnce(async (_id, _content, onDelta) => {
      onDelta("AI agents operate in changing environments.");
    })
    .mockImplementationOnce(async (_id, _content, onDelta) => {
      onDelta("Verified studies evaluate AI agents under changing environmental conditions [1].");
    });
  fireEvent.click(screen.getByRole("button", { name: "Generate Introduction" }));

  const introduction = screen.getByRole("region", { name: "Introduction section" });
  const suggestion = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });
  expect(suggestion).toHaveTextContent(
    "Verified studies evaluate AI agents under changing environmental conditions [1]."
  );
  expect(apiClient.streamChatMessage).toHaveBeenCalledTimes(2);
  expect(vi.mocked(apiClient.streamChatMessage).mock.calls[1][1]).toContain(
    "did not cite a verified source"
  );
  expect(suggestion).not.toHaveTextContent("AI agents operate in changing environments [1].");
});

it("attaches a citation only when retrieved evidence directly matches an uncited sentence", async () => {
  vi.mocked(apiClient.searchLiteratureReferences).mockResolvedValue({
    items: [{
      number: 1,
      source_id: "https://openalex.org/W-RAG",
      title: "Retrieval-Augmented Generation",
      citation: '[1] P. Lewis et al., "Retrieval-Augmented Generation," NeurIPS, 2020.',
      evidence: "Retrieval-augmented generation combines external document retrieval with language model generation.",
      url: "https://doi.org/10.5555/rag"
    }]
  });
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "Retrieval-augmented generation" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Generate Introduction" })).toBeInTheDocument());
  disableAutocomplete();

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_id, _content, onDelta) => {
    onDelta("Retrieval-augmented generation combines external document retrieval with language model generation.");
  });
  fireEvent.click(screen.getByRole("button", { name: "Generate Introduction" }));

  const introduction = screen.getByRole("region", { name: "Introduction section" });
  const suggestion = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });
  expect(suggestion).toHaveTextContent(
    "Retrieval-augmented generation combines external document retrieval with language model generation [1]."
  );
  expect(apiClient.streamChatMessage).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("region", { name: "References section" })).not.toHaveTextContent(
    "Retrieval-Augmented Generation"
  );
  fireEvent.click(within(suggestion).getByRole("button", { name: "Accept" }));
  expect(screen.getByRole("region", { name: "References section" })).toHaveTextContent(
    '[1] P. Lewis et al., "Retrieval-Augmented Generation," NeurIPS, 2020.'
  );
});

it("rejects a continuation that reuses a long phrase from the accepted text", async () => {
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "Automated research gap identification" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Generate Introduction" })).toBeInTheDocument());
  disableAutocomplete();

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_id, _content, onDelta) => {
    onDelta("The lack of systematic tools limits research gap identification in higher education [1].");
  });
  fireEvent.click(screen.getByRole("button", { name: "Generate Introduction" }));
  const introduction = screen.getByRole("region", { name: "Introduction section" });
  const firstSuggestion = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });
  fireEvent.click(within(firstSuggestion).getByRole("button", { name: "Accept" }));

  vi.mocked(apiClient.streamChatMessage)
    .mockImplementationOnce(async (_id, _content, onDelta) => {
      onDelta("The lack of systematic tools limits research gap identification in higher education and constrains educators [1].");
    })
    .mockImplementationOnce(async (_id, _content, onDelta) => {
      onDelta("This limitation matters because fragmented evidence prevents educators from prioritizing validated interventions [1].");
    });
  fireEvent.click(within(introduction).getByRole("button", { name: "Continue Introduction" }));

  const replacement = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });
  expect(replacement).toHaveTextContent("fragmented evidence prevents educators");
  expect(replacement).not.toHaveTextContent("lack of systematic tools limits research gap identification");
  expect(apiClient.streamChatMessage).toHaveBeenCalledTimes(3);
  expect(vi.mocked(apiClient.streamChatMessage).mock.calls[2][1]).toContain(
    "repeats information already present"
  );
});

it("automatically prepares the next sentence after an accepted suggestion", async () => {
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "Continuous evidence-grounded writing" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Generate Introduction" })).toBeInTheDocument());

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_id, _content, onDelta) => {
    onDelta("Evidence-grounded agents connect claims to verified sources [1].");
  });
  fireEvent.click(screen.getByRole("button", { name: "Generate Introduction" }));
  const introduction = screen.getByRole("region", { name: "Introduction section" });
  const firstSuggestion = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_id, _content, onDelta) => {
    onDelta("This grounding enables reviewers to trace the evidence behind each generated claim [1].");
  });
  fireEvent.click(within(firstSuggestion).getByRole("button", { name: "Accept" }));

  await waitFor(() => expect(
    within(introduction).getByRole("status", { name: "Introduction sentence suggestion" })
  ).toHaveTextContent("reviewers to trace the evidence"));
  expect(apiClient.streamChatMessage).toHaveBeenCalledTimes(2);
});

it("uses a prompt-first research document experience before opening the editor", async () => {
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());

  expect(screen.getByRole("heading", { name: "Untitled" })).toBeInTheDocument();
  expect(screen.getByLabelText("Document prompt")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Start research document" })).toBeDisabled();
  expect(screen.queryByRole("toolbar", { name: "Editor toolbar" })).not.toBeInTheDocument();
  expect(screen.queryByPlaceholderText("Ask ResearchOS...")).not.toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "A systematic review of autonomous scientific agents" }
  });

  expect(screen.getByText(/Strong prompt/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));

  await waitFor(() => expect(screen.getByRole("toolbar", { name: "Editor toolbar" })).toBeInTheDocument());
  expect(apiClient.streamChatMessage).not.toHaveBeenCalled();
  expect(screen.getByRole("toolbar", { name: "Editor toolbar" })).toBeInTheDocument();
  expect(screen.queryByPlaceholderText("Ask ResearchOS...")).not.toBeInTheDocument();
  fireEvent.click(within(screen.getByRole("main", { name: "Research chat" })).getByRole("button", { name: "AI Chat" }));
  expect(screen.getByPlaceholderText("Ask ResearchOS...")).toBeInTheDocument();
});

it("refreshes Library files and attaches a selected source from the prompt starter", async () => {
  vi.mocked(apiClient.listProjectFiles)
    .mockResolvedValueOnce({ items: [], total: 0 })
    .mockResolvedValueOnce({
      items: [{ id: "library-1", filename: "saved-paper.pdf", content_type: "application/pdf", status: "READY" }],
      total: 1
    });

  render(<WorkspaceShell projectId="project-1" />);
  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());

  fireEvent.click(screen.getByRole("button", { name: /Choose from Library/ }));
  expect(await screen.findByText("saved-paper.pdf")).toBeInTheDocument();
  expect(apiClient.listProjectFiles).toHaveBeenCalledTimes(2);

  fireEvent.click(screen.getByRole("button", { name: /saved-paper\.pdf Add/ }));
  expect(screen.getByRole("button", { name: /saved-paper\.pdf READY/ })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Start research document" })).toBeEnabled();
});

it("regenerates a rejected sentence without adding it to the document", async () => {
  vi.mocked(apiClient.listProjectFiles).mockResolvedValue({
    items: [{ id: "source-1", filename: "paper.pdf", status: "READY" }],
    total: 1
  });
  vi.mocked(apiClient.listProjectFileReferences).mockResolvedValue({
    items: [{
      number: 1,
      file_id: "source-1",
      filename: "paper.pdf",
      citation: '[1] A. Researcher, "Agent Evaluation," unpublished manuscript, 2025.'
    }]
  });
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "AI agent evaluation" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Generate Introduction" })).toBeInTheDocument());

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_id, _content, onDelta) => {
    onDelta("AI agents require evaluation in dynamic environments [1].");
  });
  fireEvent.click(screen.getByRole("button", { name: "Generate Introduction" }));
  const introduction = screen.getByRole("region", { name: "Introduction section" });
  const firstSuggestion = await within(introduction).findByRole("status", { name: "Introduction sentence suggestion" });

  vi.mocked(apiClient.streamChatMessage).mockImplementationOnce(async (_id, _content, onDelta) => {
    onDelta("Reliable assessment requires benchmarks that measure adaptation under environmental change [1].");
  });
  fireEvent.click(within(firstSuggestion).getByRole("button", { name: "Regenerate" }));

  await waitFor(() => expect(apiClient.streamChatMessage).toHaveBeenCalledTimes(2));
  expect(await within(introduction).findByText(/Reliable assessment requires benchmarks/)).toBeInTheDocument();
  expect(within(introduction).queryByText(/AI agents require evaluation/)).not.toBeInTheDocument();
  const regenerationRequest = vi.mocked(apiClient.streamChatMessage).mock.calls.at(-1)?.[1] ?? "";
  expect(regenerationRequest).toContain("REJECTED CANDIDATE: AI agents require evaluation in dynamic environments [1].");
});

it("reports when external scholarly search returns no verifiable sources", async () => {
  vi.mocked(apiClient.searchLiteratureReferences).mockResolvedValueOnce({ items: [] });
  render(<WorkspaceShell projectId="project-1" />);

  await waitFor(() => expect(apiClient.getConversation).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Document prompt"), {
    target: { value: "RAG evaluation" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Start research document" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Generate Introduction" })).toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "Generate Introduction" }));

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "No verifiable scholarly source was found. Refine the prompt, attach a paper, or disable citations."
  );
  expect(apiClient.streamChatMessage).not.toHaveBeenCalled();
  expect(screen.getByText("External scholarly search enabled")).toBeInTheDocument();
});
