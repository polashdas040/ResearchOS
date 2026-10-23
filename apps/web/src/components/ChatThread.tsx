import React from "react";
import { FileAttachment } from "./FileAttachment";
import { MarkdownContent } from "./MarkdownContent";
import { AttachedFile, FileReference, FileResponse } from "../lib/api-client";
import {
  CitationStyle,
  citationInstruction,
  citationMarker,
  citationStyles,
  formatReference
} from "../lib/citation-style";

const documentFonts = [
  "Times New Roman",
  "Arial",
  "Calibri",
  "Cambria",
  "Garamond",
  "Georgia",
  "Helvetica",
  "Verdana",
  "Courier New"
] as const;
const documentFontSizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32] as const;

type EditorAction =
  | "bold"
  | "italic"
  | "underline"
  | "strike"
  | "cite"
  | "image"
  | "table"
  | "equation"
  | "font-family"
  | "font-size"
  | "export"
  | "review"
  | "autocomplete-toggle"
  | "paragraph"
  | "heading-1"
  | "heading-2"
  | "heading-3";

type EditorActionDetail = {
  action: EditorAction;
  rows?: number;
  columns?: number;
  value?: string;
  alt?: string;
};

type SelectedTableCell = {
  section: string;
  tableIndex: number;
  rowIndex: number;
  columnIndex: number;
};

type ImageAlignment = "left" | "center" | "right";

type SelectedImage = {
  section: string;
  imageIndex: number;
  alignment: ImageAlignment;
};

type DocumentReview = {
  wordCount: number;
  citationCount: number;
  completedSections: number;
  totalSections: number;
  issues: string[];
};

type ChatThreadProps = {
  documentPrompt: string | null;
  sourceReferences: FileReference[];
  sourceReferencesLoaded: boolean;
  onStartDocument: (content: string) => Promise<void>;
  onGenerateSection: (content: string) => Promise<string>;
  onSearchLiterature: (query: string) => Promise<FileReference[]>;
  onToggleAiChat: () => void;
  onFileSelected?: (file: File) => Promise<void>;
  onOpenFile?: (fileId: string) => Promise<void>;
  libraryFiles?: FileResponse[];
  onAttachLibraryFile?: (file: FileResponse) => void;
  onRefreshLibrary?: () => Promise<FileResponse[]>;
  isUploadingFile?: boolean;
  attachedFiles?: AttachedFile[];
  error: string | null;
  isGenerating?: boolean;
  citationStyle: CitationStyle;
  onCitationStyleChange: (style: CitationStyle) => void;
};

export function ChatThread({
  documentPrompt,
  sourceReferences,
  sourceReferencesLoaded,
  onStartDocument,
  onGenerateSection,
  onSearchLiterature,
  onToggleAiChat,
  onFileSelected,
  onOpenFile,
  libraryFiles = [],
  onAttachLibraryFile,
  onRefreshLibrary,
  isUploadingFile = false,
  attachedFiles = [],
  error,
  isGenerating = false,
  citationStyle,
  onCitationStyleChange
}: ChatThreadProps) {
  const userPrompt = documentPrompt;
  const [documentFont, setDocumentFont] = React.useState<string>("Times New Roman");
  const [documentFontSize, setDocumentFontSize] = React.useState(10);

  return (
    <main aria-label="Research chat" className="flex h-full min-h-0 flex-col bg-white">
      {userPrompt ? (
        <EditorToolbar
          title={documentTitle(userPrompt)}
          onToggleAiChat={onToggleAiChat}
          isDisabled={isGenerating}
        />
      ) : <PromptHeader onToggleAiChat={onToggleAiChat} />}
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain bg-white">
        {userPrompt ? isGenerating ? (
          <DocumentAnalysis prompt={userPrompt} />
        ) : (
          <ResearchEditor
            prompt={userPrompt}
            sourceReferences={sourceReferences}
            sourceReferencesLoaded={sourceReferencesLoaded}
            onGenerateSection={onGenerateSection}
            onSearchLiterature={onSearchLiterature}
            onFileSelected={onFileSelected}
            onOpenFile={onOpenFile}
            isUploadingFile={isUploadingFile}
            attachedFiles={attachedFiles}
            isAnalyzing={false}
            citationStyle={citationStyle}
            onCitationStyleChange={onCitationStyleChange}
            documentFont={documentFont}
            documentFontSize={documentFontSize}
            onDocumentFontChange={setDocumentFont}
            onDocumentFontSizeChange={setDocumentFontSize}
          />
        ) : (
          <PromptStarter
            onSubmit={onStartDocument}
            onFileSelected={onFileSelected}
            onOpenFile={onOpenFile}
            libraryFiles={libraryFiles}
            onAttachLibraryFile={onAttachLibraryFile}
            onRefreshLibrary={onRefreshLibrary}
            isUploadingFile={isUploadingFile}
            attachedFiles={attachedFiles}
          />
        )}
        {error ? <p role="alert" className="mx-auto max-w-3xl px-6 pb-6 text-sm font-medium text-[#a33a2d]">{error}</p> : null}
      </div>
    </main>
  );
}

function DocumentAnalysis({ prompt }: { prompt: string }) {
  return (
    <section className="mx-auto w-full max-w-3xl px-8 py-16">
      <h1 className="text-4xl font-semibold leading-tight text-[#202124]">{documentTitle(prompt)}</h1>
      <AnalysisSkeleton />
    </section>
  );
}

function PromptHeader({ onToggleAiChat }: { onToggleAiChat: () => void }) {
  return (
    <header className="flex min-h-16 items-center justify-between border-b border-[#e5e7eb] bg-white px-5">
      <p className="text-sm font-medium text-[#202124]">Untitled</p>
      <div className="flex items-center gap-1.5">
        <button type="button" onClick={onToggleAiChat} className="rounded px-3 py-2 text-sm font-medium hover:bg-[#f5f5f7]">AI Chat</button>
        <button type="button" className="rounded bg-[#176b5b] px-3 py-2 text-sm font-semibold text-white">Research mode</button>
        <button type="button" aria-label="More options" title="More options" className="h-9 w-9 rounded text-lg hover:bg-[#f5f5f7]">...</button>
      </div>
    </header>
  );
}

function dispatchEditorAction(action: EditorAction, options: Omit<EditorActionDetail, "action"> = {}) {
  window.dispatchEvent(new CustomEvent<EditorActionDetail>("researchos:editor-action", {
    detail: { action, ...options }
  }));
}

function EditorToolbar({
  title,
  onToggleAiChat,
  isDisabled
}: {
  title: string;
  onToggleAiChat: () => void;
  isDisabled: boolean;
}) {
  const [tableDialogOpen, setTableDialogOpen] = React.useState(false);
  const [tableRows, setTableRows] = React.useState(3);
  const [tableColumns, setTableColumns] = React.useState(3);
  const [equationDialogOpen, setEquationDialogOpen] = React.useState(false);
  const [equation, setEquation] = React.useState("");
  const [imageError, setImageError] = React.useState("");
  const [autocompleteEnabled, setAutocompleteEnabled] = React.useState(true);

  function insertLocalImage(file: File) {
    if (!file.type.startsWith("image/")) {
      setImageError("Choose an image file.");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setImageError("Choose an image smaller than 2 MB.");
      return;
    }
    setImageError("");
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result !== "string") {
        setImageError("The selected image could not be read.");
        return;
      }
      dispatchEditorAction("image", {
        value: reader.result,
        alt: file.name.replace(/\.[^.]+$/, "") || "Image"
      });
    };
    reader.onerror = () => setImageError(reader.error?.message ?? "The selected image could not be read.");
    reader.readAsDataURL(file);
  }

  function runEditorCommand(command: string, value?: string) {
    document.execCommand(command, false, value);
  }

  return (
    <header className="border-b border-[#d7dde6] bg-white">
      <div className="flex min-h-14 items-center justify-between gap-3 px-5">
        <p className="min-w-0 truncate text-sm font-semibold">{title}</p>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => dispatchEditorAction("export")} className="rounded px-2 py-1.5 text-sm hover:bg-[#f1f4f6]">Export</button>
          <button type="button" onClick={() => dispatchEditorAction("review")} className="rounded px-2 py-1.5 text-sm hover:bg-[#f1f4f6]">Review</button>
          <button type="button" onClick={onToggleAiChat} className="rounded px-2 py-1.5 text-sm hover:bg-[#f1f4f6]">AI Chat</button>
          <div className="flex items-center gap-2 text-sm">
            <span>Autocomplete</span>
            <button
              type="button"
              role="switch"
              aria-label="Autocomplete"
              aria-checked={autocompleteEnabled}
              onClick={() => {
                const enabled = !autocompleteEnabled;
                setAutocompleteEnabled(enabled);
                dispatchEditorAction("autocomplete-toggle", { value: String(enabled) });
              }}
              className={`relative h-6 w-11 rounded-full transition-colors ${autocompleteEnabled ? "bg-[#176b5b]" : "bg-[#c7ced6]"}`}
            >
              <span className={`absolute top-1 h-4 w-4 rounded-full bg-white transition-transform ${autocompleteEnabled ? "left-6" : "left-1"}`} />
            </button>
          </div>
        </div>
      </div>
      <div
        role="toolbar"
        aria-label="Editor toolbar"
        className="flex min-h-12 flex-wrap items-center gap-1 border-t border-[#edf1f5] px-5 text-sm"
      >
        {["Undo", "Redo"].map((item) => (
          <button key={item} type="button" disabled={isDisabled} aria-label={item} title={item} onMouseDown={(event) => { event.preventDefault(); runEditorCommand(item.toLowerCase()); }} className="h-8 w-8 rounded hover:bg-[#f1f4f6] disabled:opacity-40">
            {item === "Undo" ? "↶" : "↷"}
          </button>
        ))}
        <select aria-label="Block style" disabled={isDisabled} defaultValue="paragraph" onChange={(event) => dispatchEditorAction(event.target.value as EditorAction)} className="h-8 rounded border border-[#d7dde6] bg-white px-2 disabled:opacity-40">
          <option value="paragraph">Paragraph</option>
          <option value="heading-1">Heading 1</option>
          <option value="heading-2">Heading 2</option>
          <option value="heading-3">Heading 3</option>
        </select>
        <select aria-label="Font family" disabled={isDisabled} defaultValue="Times New Roman" onChange={(event) => dispatchEditorAction("font-family", { value: event.target.value })} className="h-8 max-w-44 rounded border border-[#d7dde6] bg-white px-2 disabled:opacity-40">
          {documentFonts.map((font) => <option key={font} value={font}>{font}</option>)}
        </select>
        <select aria-label="Font size" disabled={isDisabled} defaultValue={10} onChange={(event) => dispatchEditorAction("font-size", { value: event.target.value })} className="h-8 w-20 rounded border border-[#d7dde6] bg-white px-2 disabled:opacity-40">
          {documentFontSizes.map((size) => <option key={size} value={size}>{size} pt</option>)}
        </select>
        <button type="button" disabled={isDisabled} aria-label="Bold" title="Bold" onMouseDown={(event) => { event.preventDefault(); dispatchEditorAction("bold"); }} className="h-8 w-8 rounded font-semibold hover:bg-[#f1f4f6] disabled:opacity-40">B</button>
        <button type="button" disabled={isDisabled} aria-label="Italic" title="Italic" onMouseDown={(event) => { event.preventDefault(); dispatchEditorAction("italic"); }} className="h-8 w-8 rounded italic hover:bg-[#f1f4f6] disabled:opacity-40">I</button>
        <button type="button" disabled={isDisabled} aria-label="Underline" title="Underline" onMouseDown={(event) => { event.preventDefault(); dispatchEditorAction("underline"); }} className="h-8 w-8 rounded underline hover:bg-[#f1f4f6] disabled:opacity-40">U</button>
        <button type="button" disabled={isDisabled} aria-label="Strike through" title="Strike through" onMouseDown={(event) => { event.preventDefault(); dispatchEditorAction("strike"); }} className="h-8 w-8 rounded line-through hover:bg-[#f1f4f6] disabled:opacity-40">S</button>
        <button type="button" disabled={isDisabled} onMouseDown={(event) => { event.preventDefault(); dispatchEditorAction("cite"); }} className="h-8 rounded px-2 font-semibold hover:bg-[#f1f4f6] disabled:opacity-40">Cite</button>
        <label className={`flex h-8 cursor-pointer items-center rounded px-2 hover:bg-[#f1f4f6] ${isDisabled ? "pointer-events-none opacity-40" : ""}`}>
          Image
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            aria-label="Insert image from device"
            className="sr-only"
            disabled={isDisabled}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) insertLocalImage(file);
            }}
          />
        </label>
        <button type="button" disabled={isDisabled} onClick={() => setTableDialogOpen(true)} className="h-8 rounded px-2 hover:bg-[#f1f4f6] disabled:opacity-40">Table</button>
        <button type="button" disabled={isDisabled} onMouseDown={(event) => { event.preventDefault(); setEquationDialogOpen(true); }} className="h-8 rounded px-2 hover:bg-[#f1f4f6] disabled:opacity-40">Equation</button>
      </div>
      {imageError ? <p role="alert" className="px-5 pb-2 text-xs text-[#b44635]">{imageError}</p> : null}
      {tableDialogOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 p-4">
          <section role="dialog" aria-modal="true" aria-label="Insert table" className="w-full max-w-sm rounded-lg border border-[#cfd7df] bg-white p-5 shadow-xl">
            <h2 className="text-lg font-semibold">Insert table</h2>
            <p className="mt-1 text-sm text-[#667386]">Choose the number of rows and columns.</p>
            <div className="mt-5 grid grid-cols-2 gap-4">
              <label className="text-sm font-medium">
                Rows
                <input aria-label="Table rows" type="number" min={1} max={20} value={tableRows} onChange={(event) => setTableRows(clampTableDimension(event.target.value))} className="mt-1.5 h-10 w-full rounded border border-[#cfd7df] px-3" />
              </label>
              <label className="text-sm font-medium">
                Columns
                <input aria-label="Table columns" type="number" min={1} max={12} value={tableColumns} onChange={(event) => setTableColumns(clampTableDimension(event.target.value, 12))} className="mt-1.5 h-10 w-full rounded border border-[#cfd7df] px-3" />
              </label>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button type="button" onClick={() => setTableDialogOpen(false)} className="rounded border border-[#c5cfda] px-3 py-2 text-sm">Cancel</button>
              <button type="button" onClick={() => { dispatchEditorAction("table", { rows: tableRows, columns: tableColumns }); setTableDialogOpen(false); }} className="rounded bg-[#176b5b] px-3 py-2 text-sm font-semibold text-white">Insert table</button>
            </div>
          </section>
        </div>
      ) : null}
      {equationDialogOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 p-4">
          <section role="dialog" aria-modal="true" aria-label="Insert equation" className="w-full max-w-md rounded-lg border border-[#cfd7df] bg-white p-5 shadow-xl">
            <h2 className="text-lg font-semibold">Insert equation</h2>
            <label className="mt-4 block text-sm font-medium">
              Equation
              <input autoFocus aria-label="Equation" value={equation} onChange={(event) => setEquation(event.target.value)} placeholder="e.g. E = mc^2" className="mt-1.5 h-10 w-full rounded border border-[#cfd7df] px-3 font-serif" />
            </label>
            <div className="mt-6 flex justify-end gap-2">
              <button type="button" onClick={() => { setEquationDialogOpen(false); setEquation(""); }} className="rounded border border-[#c5cfda] px-3 py-2 text-sm">Cancel</button>
              <button type="button" disabled={!equation.trim()} onClick={() => { dispatchEditorAction("equation", { value: equation.trim() }); setEquationDialogOpen(false); setEquation(""); }} className="rounded bg-[#176b5b] px-3 py-2 text-sm font-semibold text-white disabled:opacity-50">Insert equation</button>
            </div>
          </section>
        </div>
      ) : null}
    </header>
  );
}

type PromptStarterProps = Pick<
  ChatThreadProps,
  "onFileSelected" | "onOpenFile" | "isUploadingFile" | "attachedFiles" | "libraryFiles" | "onAttachLibraryFile" | "onRefreshLibrary"
>;

function PromptStarter({
  onSubmit,
  onFileSelected,
  onOpenFile,
  libraryFiles = [],
  onAttachLibraryFile,
  onRefreshLibrary,
  isUploadingFile = false,
  attachedFiles = []
}: PromptStarterProps & { onSubmit: (content: string) => Promise<void> }) {
  const [prompt, setPrompt] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [pdfImportError, setPdfImportError] = React.useState("");
  const [libraryOpen, setLibraryOpen] = React.useState(false);
  const [pickerFiles, setPickerFiles] = React.useState<FileResponse[]>(libraryFiles);
  const [isRefreshingLibrary, setIsRefreshingLibrary] = React.useState(false);
  const [libraryError, setLibraryError] = React.useState("");
  const trimmedPrompt = prompt.trim();
  const canSubmit = Boolean(trimmedPrompt || attachedFiles.length > 0);
  const isStrongPrompt = trimmedPrompt.length >= 40;

  React.useEffect(() => {
    setPickerFiles(libraryFiles);
  }, [libraryFiles]);

  async function toggleLibrary() {
    const nextOpen = !libraryOpen;
    setLibraryOpen(nextOpen);
    if (!nextOpen || !onRefreshLibrary) return;

    setIsRefreshingLibrary(true);
    setLibraryError("");
    try {
      setPickerFiles(await onRefreshLibrary());
    } catch (refreshError) {
      setLibraryError(refreshError instanceof Error ? refreshError.message : "Could not load Library files.");
    } finally {
      setIsRefreshingLibrary(false);
    }
  }

  async function startDocument() {
    if (!canSubmit || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onSubmit(trimmedPrompt);
      setPrompt("");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function importPdf(file: File) {
    const isPdf = file.name.toLowerCase().endsWith(".pdf") && (
      !file.type || file.type === "application/pdf"
    );
    if (!isPdf) {
      setPdfImportError("Choose a PDF document.");
      return;
    }
    setPdfImportError("");
    await onFileSelected?.(file);
    const title = file.name.replace(/\.pdf$/i, "").replace(/[_-]+/g, " ").trim();
    setPrompt((current) => current || (
      `Analyze the imported PDF "${title}" and create an evidence-grounded research document ` +
      "that preserves its key findings, methods, limitations, and references."
    ));
  }

  return (
    <section className="mx-auto flex w-full max-w-3xl flex-col px-6 py-8 sm:py-12">
      <h1 className="text-center text-4xl font-semibold text-[#a8aaaf]">Untitled</h1>
      <div className="mt-8 rounded-lg border border-[#dedfe3] bg-white p-5 shadow-[0_1px_2px_rgba(0,0,0,0.04)]">
        <div className="flex items-center justify-between gap-3">
          <p className="text-base font-semibold text-[#202124]">Fill document prompt</p>
          <span aria-hidden="true" className="text-[#737780]">⌄</span>
        </div>
        <textarea
          aria-label="Document prompt"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="Describe your research topic, question, document, or intended outcome"
          className="mt-4 min-h-28 w-full resize-none rounded-lg border border-[#176b5b] bg-white p-4 text-base leading-6 text-[#202124] outline-none placeholder:text-[#a3a6ad] focus:ring-2 focus:ring-[#176b5b]/15"
        />
        {attachedFiles.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {attachedFiles.map((file) => (
              <button
                key={file.id}
                type="button"
                onClick={() => void onOpenFile?.(file.id)}
                className="rounded border border-[#d7dde6] bg-[#f8fafc] px-3 py-2 text-xs font-medium"
              >
                {file.filename} <span className="ml-1 text-[#176b5b]">{file.status}</span>
              </button>
            ))}
          </div>
        ) : null}
        <div className="mt-4 h-1 overflow-hidden rounded-full bg-[#eef0f2]">
          <div className={`h-full rounded-full transition-all ${isStrongPrompt ? "w-full bg-[#176b5b]" : trimmedPrompt ? "w-1/2 bg-[#e5a229]" : "w-0"}`} />
        </div>
        <p className="mt-3 text-sm text-[#737780]">
          <strong className="text-[#202124]">{isStrongPrompt ? "Strong prompt" : "Weak prompt"}:</strong>{" "}
          {isStrongPrompt ? "Enough context to plan the research workflow" : "Add more context for higher quality generations"}
        </p>
        <div className="my-5 flex items-center gap-3 text-xs text-[#8b8e95]">
          <span className="h-px flex-1 bg-[#eceef0]" />
          <span>or also</span>
          <span className="h-px flex-1 bg-[#eceef0]" />
        </div>
        <label className={`mb-3 flex min-h-16 items-center gap-3 rounded-lg border border-[#dedfe3] bg-[#fafafa] px-4 py-3 text-sm text-[#202124] ${isUploadingFile ? "cursor-not-allowed opacity-60" : "cursor-pointer hover:border-[#9fbab2]"}`}>
          <span className="flex h-9 w-9 items-center justify-center rounded bg-[#fce9e7] text-xs font-bold text-[#b42318]">PDF</span>
          <span className="min-w-0 flex-1">
            <span className="block font-medium">{isUploadingFile ? "Importing PDF..." : "Import PDF document"}</span>
            <span className="mt-0.5 block text-xs text-[#737780]">Analyze its text and use it as verified writing context</span>
          </span>
          <span aria-hidden="true" className="text-[#8b8e95]">›</span>
          <input
            type="file"
            className="sr-only"
            accept=".pdf,application/pdf"
            aria-label="Import PDF document"
            disabled={isUploadingFile}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) void importPdf(file);
              event.target.value = "";
            }}
          />
        </label>
        {pdfImportError ? <p role="alert" className="mb-3 text-xs font-medium text-[#a33a2d]">{pdfImportError}</p> : null}
        <FileAttachment onFileSelected={onFileSelected} disabled={isUploadingFile} variant="source" />
        <button
          type="button"
          aria-expanded={libraryOpen}
          aria-controls="prompt-library-files"
          onClick={() => void toggleLibrary()}
          className="mt-3 flex min-h-16 w-full items-center gap-3 rounded-lg border border-[#dedfe3] bg-[#fafafa] px-4 py-3 text-left text-sm hover:border-[#9fbab2]"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded bg-[#e7f1ee] font-semibold text-[#176b5b]">L</span>
          <span className="min-w-0 flex-1">
            <span className="block font-medium">Choose from Library</span>
            <span className="mt-0.5 block text-xs text-[#737780]">Use a source already saved in ResearchOS</span>
          </span>
          <span aria-hidden="true" className={`h-2 w-2 border-b border-r border-[#667386] transition-transform ${libraryOpen ? "rotate-[-135deg]" : "rotate-45"}`} />
        </button>
        {libraryOpen ? (
          <div id="prompt-library-files" className="mt-2 max-h-52 overflow-y-auto overscroll-contain rounded-lg border border-[#d7dde6] bg-white p-2">
            {isRefreshingLibrary ? <p role="status" className="px-3 py-4 text-sm text-[#667386]">Loading Library...</p> : null}
            {!isRefreshingLibrary && libraryError ? <p role="alert" className="px-3 py-4 text-sm text-[#a33a2d]">{libraryError}</p> : null}
            {!isRefreshingLibrary && !libraryError && pickerFiles.length > 0 ? pickerFiles.map((file) => {
              const selected = attachedFiles.some((attached) => attached.id === file.id);
              return (
                <button
                  key={file.id}
                  type="button"
                  disabled={selected}
                  onClick={() => {
                    onAttachLibraryFile?.(file);
                    setLibraryOpen(false);
                  }}
                  className="flex w-full items-center justify-between gap-3 rounded px-3 py-2 text-left text-sm hover:bg-[#f1f5f4] disabled:opacity-60"
                >
                  <span className="truncate">{file.filename}</span>
                  <span className="shrink-0 text-xs font-medium text-[#176b5b]">{selected ? "Selected" : "Add"}</span>
                </button>
              );
            }) : null}
            {!isRefreshingLibrary && !libraryError && pickerFiles.length === 0 ? <p className="px-3 py-4 text-sm text-[#667386]">No files saved in this project's Library yet.</p> : null}
          </div>
        ) : null}
        <button
          type="button"
          aria-label="Start research document"
          disabled={!canSubmit || isSubmitting}
          onClick={() => void startDocument()}
          className="mt-4 ml-auto block rounded bg-[#176b5b] px-5 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-[#b9d2cc]"
        >
          {isSubmitting ? "Starting..." : "Next"}
        </button>
      </div>
      <button type="button" className="mx-auto mt-4 text-sm font-medium text-[#737780] hover:text-[#202124]">Skip and start writing</button>
      <p className="mt-10 text-sm font-medium text-[#737780]">Explore</p>
      <div className="mt-8 grid w-full max-w-2xl gap-3 sm:grid-cols-2">
        <button type="button" className="rounded-lg border border-[#dedfe3] p-4 text-left hover:bg-[#f8fafc]">
          <span className="block text-lg" aria-hidden="true">◯</span>
          <span className="mt-2 block font-semibold">Chat with AI</span>
          <span className="mt-1 block text-sm leading-5 text-[#737780]">Discover papers, brainstorm ideas, or write a draft.</span>
        </button>
        <label className="cursor-pointer rounded-lg border border-[#dedfe3] p-4 text-left hover:bg-[#f8fafc]">
          <span className="block text-lg" aria-hidden="true">⇧</span>
          <span className="mt-2 block font-semibold">Upload Sources</span>
          <span className="mt-1 block text-sm leading-5 text-[#737780]">Upload PDFs and datasets to cite or provide context to AI.</span>
          <input
            type="file"
            className="sr-only"
            accept=".pdf,application/pdf,.csv,text/csv,.json,application/json,.txt,text/plain"
            aria-label="Upload source"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) void onFileSelected?.(file);
              event.target.value = "";
            }}
          />
        </label>
      </div>
    </section>
  );
}

type ResearchEditorProps = {
  prompt: string;
  sourceReferences: FileReference[];
  sourceReferencesLoaded: boolean;
  onGenerateSection: (content: string) => Promise<string>;
  onSearchLiterature: (query: string) => Promise<FileReference[]>;
  onFileSelected?: (file: File) => Promise<void>;
  onOpenFile?: (fileId: string) => Promise<void>;
  isUploadingFile: boolean;
  attachedFiles: AttachedFile[];
  isAnalyzing: boolean;
  citationStyle: CitationStyle;
  onCitationStyleChange: (style: CitationStyle) => void;
  documentFont: string;
  documentFontSize: number;
  onDocumentFontChange: (font: string) => void;
  onDocumentFontSizeChange: (size: number) => void;
};

function ResearchEditor({
  prompt,
  sourceReferences,
  sourceReferencesLoaded,
  onGenerateSection,
  onSearchLiterature,
  onFileSelected,
  onOpenFile,
  isUploadingFile,
  attachedFiles,
  isAnalyzing,
  citationStyle,
  onCitationStyleChange,
  documentFont,
  documentFontSize,
  onDocumentFontChange,
  onDocumentFontSizeChange
}: ResearchEditorProps) {
  const sections = ["Introduction", "Literature Review", "Methodology", "Results", "Discussion", "Conclusion"];
  const [title, setTitle] = React.useState(() => documentTitle(prompt));
  const [sectionTitles, setSectionTitles] = React.useState<Record<string, string>>(() =>
    Object.fromEntries(sections.map((section) => [section, section]))
  );
  const [activeSection, setActiveSection] = React.useState("Introduction");
  const [contextOpen, setContextOpen] = React.useState(false);
  const [sourceListOpen, setSourceListOpen] = React.useState(false);
  const [includeConversation, setIncludeConversation] = React.useState(true);
  const [includeProjectSources, setIncludeProjectSources] = React.useState(true);
  const [searchWeb, setSearchWeb] = React.useState(true);
  const [requireCitations, setRequireCitations] = React.useState(true);
  const [pendingSection, setPendingSection] = React.useState<string | null>(null);
  const [generatedSections, setGeneratedSections] = React.useState<Record<string, string>>({});
  const [draftSectionsForReferences, setDraftSectionsForReferences] = React.useState<Record<string, string>>({});
  const [editorRevisions, setEditorRevisions] = React.useState<Record<string, number>>({});
  const [sentenceSuggestions, setSentenceSuggestions] = React.useState<Record<string, string>>({});
  const [selectedTableCell, setSelectedTableCell] = React.useState<SelectedTableCell | null>(null);
  const [selectedImage, setSelectedImage] = React.useState<SelectedImage | null>(null);
  const [discoveredReferences, setDiscoveredReferences] = React.useState<FileReference[]>([]);
  const [referenceOrder, setReferenceOrder] = React.useState<string[]>([]);
  const [suggestionError, setSuggestionError] = React.useState<Record<string, string>>({});
  const [autocompleteEnabled, setAutocompleteEnabled] = React.useState(true);
  const [reviewReport, setReviewReport] = React.useState<DocumentReview | null>(null);
  const [exportOpen, setExportOpen] = React.useState(false);
  const [exportStatus, setExportStatus] = React.useState("");
  const [sectionPrompts, setSectionPrompts] = React.useState<Record<string, string>>(() =>
    Object.fromEntries(sections.map((section) => [section, defaultSectionPrompt(section, prompt)]))
  );
  const generatedSectionsRef = React.useRef<Record<string, string>>({});
  const sectionEditorRefs = React.useRef<Record<string, HTMLDivElement | null>>({});
  const editorSelectionRefs = React.useRef<Record<string, Range | null>>({});
  const articleRef = React.useRef<HTMLElement | null>(null);
  const [draftLoaded, setDraftLoaded] = React.useState(false);
  const draftKey = `researchos.document.${encodeURIComponent(prompt)}`;

  React.useEffect(() => {
    try {
      const stored = window.localStorage.getItem(draftKey);
      if (stored) {
        const draft = JSON.parse(stored) as {
          title?: string;
          sectionTitles?: Record<string, string>;
          sectionPrompts?: Record<string, string>;
          generatedSections?: Record<string, string>;
          discoveredReferences?: FileReference[];
          referenceOrder?: string[];
          documentFont?: string;
          documentFontSize?: number;
        };
        if (draft.title) setTitle(draft.title);
        if (draft.sectionTitles) setSectionTitles((current) => ({ ...current, ...draft.sectionTitles }));
        if (draft.sectionPrompts) setSectionPrompts((current) => ({ ...current, ...draft.sectionPrompts }));
        if (draft.generatedSections) setGeneratedSections(draft.generatedSections);
        if (draft.discoveredReferences) setDiscoveredReferences(draft.discoveredReferences);
        if (draft.referenceOrder) setReferenceOrder(draft.referenceOrder);
        if (draft.documentFont && documentFonts.includes(draft.documentFont as typeof documentFonts[number])) {
          onDocumentFontChange(draft.documentFont);
        }
        if (draft.documentFontSize && documentFontSizes.includes(draft.documentFontSize as typeof documentFontSizes[number])) {
          onDocumentFontSizeChange(draft.documentFontSize);
        }
      }
    } finally {
      setDraftLoaded(true);
    }
  }, [draftKey]);

  React.useEffect(() => {
    if (!draftLoaded) return;
    window.localStorage.setItem(draftKey, JSON.stringify({
      title,
      sectionTitles,
      sectionPrompts,
      generatedSections,
      discoveredReferences,
      referenceOrder,
      documentFont,
      documentFontSize
    }));
  }, [discoveredReferences, documentFont, documentFontSize, draftKey, draftLoaded, generatedSections, referenceOrder, sectionPrompts, sectionTitles, title]);

  React.useEffect(() => {
    generatedSectionsRef.current = generatedSections;
    setDraftSectionsForReferences(generatedSections);
  }, [generatedSections]);

  React.useEffect(() => {
    for (const editor of Object.values(sectionEditorRefs.current)) {
      editor?.querySelectorAll<HTMLElement>("th, td").forEach((cell) => {
        cell.style.boxShadow = "";
        cell.removeAttribute("aria-selected");
      });
    }
    if (!selectedTableCell) return;
    const editor = sectionEditorRefs.current[selectedTableCell.section];
    const table = editor?.querySelectorAll("table")[selectedTableCell.tableIndex] as HTMLTableElement | undefined;
    const cell = table?.rows[selectedTableCell.rowIndex]?.cells[selectedTableCell.columnIndex];
    if (cell) {
      cell.style.boxShadow = "inset 0 0 0 2px #176b5b";
      cell.setAttribute("aria-selected", "true");
    }
  }, [editorRevisions, selectedTableCell]);

  React.useEffect(() => {
    for (const editor of Object.values(sectionEditorRefs.current)) {
      editor?.querySelectorAll<HTMLElement>("img").forEach((image) => {
        image.style.boxShadow = "";
        image.removeAttribute("aria-selected");
      });
    }
    if (!selectedImage) return;
    const image = sectionEditorRefs.current[selectedImage.section]
      ?.querySelectorAll("img")[selectedImage.imageIndex] as HTMLImageElement | undefined;
    if (image) {
      image.style.boxShadow = "0 0 0 2px #176b5b";
      image.setAttribute("aria-selected", "true");
    }
  }, [editorRevisions, selectedImage]);

  const allReferences = React.useMemo(
    () => orderReferenceCatalog(combineReferences(sourceReferences, discoveredReferences), referenceOrder),
    [discoveredReferences, referenceOrder, sourceReferences]
  );

  React.useEffect(() => {
    if (!draftLoaded || !sourceReferencesLoaded) return;
    const normalized = Object.fromEntries(
      Object.entries(generatedSections).map(([section, content]) => [
        section,
        normalizeVerifiedCitations(content, allReferences, citationStyle)
      ])
    );
    const compacted = compactDocumentCitations(normalized, allReferences, sections, "", "", citationStyle);
    if (!sameStringArray(referenceOrder, compacted.referenceOrder)) {
      setReferenceOrder(compacted.referenceOrder);
    }
    if (Object.keys(generatedSections).some(
      (section) => compacted.sections[section] !== generatedSections[section]
    )) {
      generatedSectionsRef.current = compacted.sections;
      setGeneratedSections(compacted.sections);
    }
  }, [allReferences, citationStyle, draftLoaded, generatedSections, referenceOrder, sourceReferencesLoaded]);

  function updateSectionContent(section: string, content: string, commit: boolean) {
    generatedSectionsRef.current = { ...generatedSectionsRef.current, [section]: content };
    if (commit) {
      setGeneratedSections((current) => ({ ...current, [section]: content }));
    }
  }

  function editSelectedTable(action: "row-above" | "row-below" | "column-left" | "column-right" | "delete-row" | "delete-column" | "delete-table") {
    if (!selectedTableCell) return;
    const section = selectedTableCell.section;
    const result = editMarkdownTable(
      generatedSectionsRef.current[section] ?? "",
      selectedTableCell,
      action
    );
    if (!result) return;
    const content = result.content;
    updateSectionContent(selectedTableCell.section, content, true);
    setDraftSectionsForReferences((current) => ({ ...current, [selectedTableCell.section]: content }));
    setEditorRevisions((current) => ({ ...current, [selectedTableCell.section]: (current[selectedTableCell.section] ?? 0) + 1 }));
    setSelectedTableCell(result.selection);
  }

  function alignSelectedImage(alignment: ImageAlignment) {
    if (!selectedImage) return;
    const editor = sectionEditorRefs.current[selectedImage.section];
    const image = editor?.querySelectorAll("img")[selectedImage.imageIndex] as HTMLImageElement | undefined;
    if (!editor || !image) return;
    let wrapper = image.closest<HTMLElement>("[data-image-align]");
    if (!wrapper) {
      wrapper = document.createElement("span");
      image.parentNode?.insertBefore(wrapper, image);
      wrapper.append(image);
    }
    wrapper.dataset.imageAlign = alignment;
    const content = editorContentToMarkdown(editor);
    updateSectionContent(selectedImage.section, content, true);
    setDraftSectionsForReferences((current) => ({ ...current, [selectedImage.section]: content }));
    setEditorRevisions((current) => ({ ...current, [selectedImage.section]: (current[selectedImage.section] ?? 0) + 1 }));
    setSelectedImage({ ...selectedImage, alignment });
  }

  function snapshotDocument() {
    const snapshot = { ...generatedSectionsRef.current };
    for (const documentSection of sections) {
      const editor = sectionEditorRefs.current[documentSection];
      if (editor) snapshot[documentSection] = editorContentToMarkdown(editor);
    }
    generatedSectionsRef.current = snapshot;
    setGeneratedSections(snapshot);
    return snapshot;
  }

  function rememberEditorSelection(section: string, editor: HTMLElement) {
    const selection = window.getSelection();
    if (!selection?.rangeCount) return;
    const range = selection.getRangeAt(0);
    if (editor.contains(range.commonAncestorContainer)) {
      editorSelectionRefs.current[section] = range.cloneRange();
    }
  }

  function exportMarkup() {
    snapshotDocument();
    if (!articleRef.current) return "";
    const manuscript = articleRef.current.cloneNode(true) as HTMLElement;
    manuscript.querySelectorAll("button, [role='toolbar'], [aria-label$='sentence suggestion']").forEach((node) => node.remove());
    manuscript.querySelectorAll<HTMLElement>("[contenteditable]").forEach((node) => node.removeAttribute("contenteditable"));
    manuscript.querySelectorAll<HTMLElement>("[aria-selected]").forEach((node) => {
      node.removeAttribute("aria-selected");
      node.style.boxShadow = "";
    });
    return buildExportHtml(title, manuscript.innerHTML, documentFont, documentFontSize);
  }

  function exportWordDocument() {
    const markup = exportMarkup();
    if (!markup) return;
    downloadBlob(
      new Blob(["\ufeff", markup], { type: "application/msword;charset=utf-8" }),
      `${exportFilename(title)}.doc`
    );
    setExportStatus("Word document downloaded.");
  }

  function exportPdfDocument() {
    const markup = exportMarkup();
    if (!markup) return;
    const frame = document.createElement("iframe");
    frame.setAttribute("title", "PDF export preview");
    frame.style.position = "fixed";
    frame.style.width = "1px";
    frame.style.height = "1px";
    frame.style.right = "0";
    frame.style.bottom = "0";
    frame.style.border = "0";
    document.body.append(frame);
    const frameDocument = frame.contentDocument;
    if (!frameDocument || !frame.contentWindow) {
      frame.remove();
      setExportStatus("PDF export could not be opened.");
      return;
    }
    frameDocument.open();
    frameDocument.write(markup);
    frameDocument.close();
    window.setTimeout(() => {
      frame.contentWindow?.focus();
      frame.contentWindow?.print();
      window.setTimeout(() => frame.remove(), 1_000);
    }, 100);
    setExportStatus("Choose Save as PDF in the print dialog.");
  }

  React.useEffect(() => {
    function handleEditorAction(event: Event) {
      const detail = (event as CustomEvent<EditorActionDetail>).detail;
      const action = detail.action;
      if (action === "export") {
        snapshotDocument();
        setExportStatus("");
        setExportOpen(true);
        return;
      }
      if (action === "review") {
        setReviewReport(createDocumentReview(snapshotDocument(), sections));
        return;
      }
      if (action === "autocomplete-toggle") {
        setAutocompleteEnabled(detail.value === "true");
        return;
      }
      const editor = sectionEditorRefs.current[activeSection];
      if (!editor) return;
      const savedRange = editorSelectionRefs.current[activeSection];
      if (savedRange && editor.contains(savedRange.commonAncestorContainer)) {
        const selection = window.getSelection();
        selection?.removeAllRanges();
        selection?.addRange(savedRange);
      }

      if (action === "image") {
        if (!detail.value?.startsWith("data:image/")) return;
        const alt = (detail.alt ?? "Image").replace(/[\[\]]/g, "");
        insertMarkdownAtSelection(editor, `![${alt}](${detail.value})`);
      } else if (action === "table") {
        insertTableAtSelection(editor, detail.rows ?? 3, detail.columns ?? 3);
      } else if (action === "cite") {
        if (!allReferences.length) {
          setSuggestionError((current) => ({ ...current, [activeSection]: "Attach or find a verified source before inserting a citation." }));
          return;
        }
        const requestedNumber = allReferences.length === 1
          ? 1
          : Number(window.prompt(`Reference number (1-${allReferences.length})`, "1"));
        const reference = allReferences[requestedNumber - 1];
        if (!reference) {
          setSuggestionError((current) => ({ ...current, [activeSection]: "Choose a valid reference number from the available source list." }));
          return;
        }
        insertMarkdownAtSelection(editor, citationMarker(reference, citationStyle));
      } else if (action === "equation") {
        if (!detail.value?.trim()) return;
        insertMarkdownAtSelection(editor, `$${detail.value.trim()}$`);
      } else if (action === "font-family") {
        applyStyleToSelection(editor, "fontFamily", detail.value ?? "Times New Roman");
      } else if (action === "font-size") {
        applyStyleToSelection(editor, "fontSize", `${Number(detail.value) || 10}pt`);
      } else if (action === "bold") {
        toggleSelectionFormat(editor, "bold", "strong");
      } else if (action === "italic") {
        toggleSelectionFormat(editor, "italic", "em");
      } else if (action === "underline") {
        toggleSelectionFormat(editor, "underline", "u");
      } else if (action === "strike") {
        toggleSelectionFormat(editor, "strikeThrough", "s");
      } else {
        const headingPrefix = action === "heading-1" ? "# " : action === "heading-2" ? "## " : action === "heading-3" ? "### " : "";
        formatSelectedBlocks(editor, headingPrefix);
      }

      const content = editorContentToMarkdown(editor);
      editor.replaceChildren();
      updateSectionContent(activeSection, content, true);
      setDraftSectionsForReferences((current) => ({ ...current, [activeSection]: content }));
      setEditorRevisions((current) => ({ ...current, [activeSection]: (current[activeSection] ?? 0) + 1 }));
    }

    window.addEventListener("researchos:editor-action", handleEditorAction);
    return () => window.removeEventListener("researchos:editor-action", handleEditorAction);
  }, [activeSection, allReferences, citationStyle]);

  async function generateSection(
    section: string,
    rejectedCandidate = "",
    documentOverride?: Record<string, string>
  ) {
    const documentSnapshot = documentOverride ?? snapshotDocument();
    setPendingSection(section);
    setSuggestionError((current) => ({ ...current, [section]: "" }));
    const currentSectionContent = documentSnapshot[section]?.trim() ?? "";
    const rhetoricalMove = nextRhetoricalMove(section, currentSectionContent);
    const contextInstructions = [
      includeConversation ? "use the conversation context" : null,
      includeProjectSources ? "use attached project sources" : null,
      searchWeb ? "search external scholarly sources" : null,
      requireCitations ? "include verifiable citations for factual claims" : null
    ].filter(Boolean).join(", ");
    const existingDocument = sections
      .map((documentSection) => {
        const content = documentSnapshot[documentSection]?.trim();
        return content ? `## ${sectionTitles[documentSection]}\n${content}` : null;
      })
      .filter(Boolean)
      .join("\n\n")
      .slice(0, 24_000);
    const continuityInstruction = existingDocument
      ? `\n\nEXISTING DOCUMENT (read this before writing and preserve its terminology, claims, and narrative continuity):\n${existingDocument}`
      : "\n\nEXISTING DOCUMENT: No sections have been drafted yet.";
    try {
      let generationReferences = allReferences;
      let currentSearchReferences: FileReference[] = [];
      if (requireCitations && (searchWeb || generationReferences.length === 0)) {
        const found = await onSearchLiterature(
          `${title}. ${section}. ${rhetoricalMove}. ${sectionPrompts[section]}. ${currentSectionContent.slice(-400)}`.slice(0, 1000)
        );
        currentSearchReferences = found;
        generationReferences = combineReferences(allReferences, found);
        setDiscoveredReferences((current) => combineReferences(current, found));
      }
      if (requireCitations && generationReferences.length === 0) {
        setSuggestionError((current) => ({
          ...current,
          [section]: "No verifiable scholarly source was found. Refine the prompt, attach a paper, or disable citations."
        }));
        return;
      }
      const preferredEvidence = [
        ...(includeProjectSources ? sourceReferences : []),
        ...(currentSearchReferences.length > 0 ? currentSearchReferences : generationReferences)
      ];
      const evidenceIds = [...new Set(preferredEvidence.map((reference) => reference.file_id))];
      const contextReferences = evidenceIds
        .map((sourceId) => generationReferences.find((reference) => reference.file_id === sourceId))
        .filter((reference): reference is FileReference => Boolean(reference?.evidence?.trim()))
        .slice(0, 6);
      const validSourceIds = new Set([
        ...(includeProjectSources ? sourceReferences : []),
        ...contextReferences
      ].map((reference) => reference.file_id));
      const validatedReferences = generationReferences.filter((reference) => validSourceIds.has(reference.file_id));
      const scholarlyContext = buildScholarlyContext(contextReferences, citationStyle);
      const allowedCitations = validatedReferences.map((reference) => citationMarker(reference, citationStyle)).join(", ");
      let lastCandidate = rejectedCandidate;
      let validationFailure = "";
      for (let attempt = 0; attempt < 3; attempt += 1) {
        const rejectionInstruction = lastCandidate
          ? `\nREJECTED CANDIDATE: ${lastCandidate}\nREJECTION REASON: ${validationFailure || "The user requested a different sentence."}\nGenerate a materially different sentence that fixes this problem.`
          : "";
        const generatedContent = await onGenerateSection(
          `Write the next sentence of the ${section} section for \"${title}\". Context policy: ${contextInstructions || "use only supplied context"}.\n` +
          `SECTION GUIDANCE:\n${sectionPrompts[section]}\n` +
          `NEXT RHETORICAL MOVE: ${rhetoricalMove}\n` +
          "Advance this rhetorical move rather than restating the topic, problem, or preceding sentence. " +
          "Use the verified scholarly evidence below as the primary evidence. Cite every factual claim from a paper " +
          `using ${citationInstruction(citationStyle)}. Page labels in the evidence context are for verification only; ` +
          "do not include page locators in the manuscript citation. " +
          "Select the source whose supplied evidence directly supports the sentence; do not default to source [1]. " +
          `End the sentence with at least one citation from this allowed list: ${allowedCitations || "none"}. ` +
          "Place citations before the sentence's final punctuation. " +
          "Never invent authors, years, findings, page numbers, or references. If evidence is insufficient, say so explicitly. " +
          "Return exactly one complete sentence of polished academic prose and nothing else: no heading, preface, list, or second sentence. " +
          "The sentence must connect logically to the final accepted sentence, add a distinct claim, and never paraphrase or repeat existing text." +
          rejectionInstruction +
          continuityInstruction +
          scholarlyContext
        );
        let sentence = normalizeVerifiedCitations(
          firstCompleteSentence(generatedContent),
          validatedReferences,
          citationStyle
        );
        if (requireCitations && !hasVerifiedCitation(sentence, validatedReferences, citationStyle)) {
          sentence = attachBestEvidenceCitation(sentence, validatedReferences, citationStyle);
          if (!hasVerifiedCitation(sentence, validatedReferences, citationStyle)) {
            lastCandidate = sentence;
            validationFailure = "The sentence did not cite a verified source that directly supports its claim.";
            continue;
          }
        }
        const repeatsDraft = isNearDuplicate(sentence, currentSectionContent);
        const repeatsRejectedCandidate = Boolean(
          rejectedCandidate && isSameSentence(sentence, rejectedCandidate)
        );
        if (sentence && !repeatsDraft && !repeatsRejectedCandidate) {
          const compacted = compactDocumentCitations(
            documentSnapshot,
            generationReferences,
            sections,
            section,
            sentence,
            citationStyle
          );
          generatedSectionsRef.current = compacted.sections;
          setGeneratedSections(compacted.sections);
          setReferenceOrder(compacted.referenceOrder);
          setEditorRevisions((current) => Object.fromEntries(
            sections.map((documentSection) => [documentSection, (current[documentSection] ?? 0) + 1])
          ));
          setSentenceSuggestions((current) => ({ ...current, [section]: compacted.pendingContent }));
          return;
        }
        lastCandidate = sentence;
        validationFailure = repeatsRejectedCandidate
          ? "The sentence repeats the candidate rejected by the user."
          : "The sentence repeats information already present in the section.";
      }
      setSuggestionError((current) => ({
        ...current,
        [section]: validationFailure || "The model could not produce a supported, non-repetitive sentence."
      }));
    } catch (error) {
      setSuggestionError((current) => ({
        ...current,
        [section]: error instanceof Error ? error.message : "Scholarly source search failed."
      }));
    } finally {
      setPendingSection(null);
    }
  }

  function acceptSuggestion(section: string) {
    const suggestion = sentenceSuggestions[section]?.trim();
    if (!suggestion) return;
    const liveContent = sectionEditorRefs.current[section]?.textContent?.trim()
      ?? generatedSectionsRef.current[section]?.trim()
      ?? "";
    const content = liveContent ? `${liveContent} ${suggestion}` : suggestion;
    const compacted = compactDocumentCitations(
      { ...generatedSectionsRef.current, [section]: content },
      allReferences,
      sections,
      "",
      "",
      citationStyle
    );
    generatedSectionsRef.current = compacted.sections;
    setReferenceOrder(compacted.referenceOrder);
    setGeneratedSections(compacted.sections);
    setEditorRevisions((current) => Object.fromEntries(
      sections.map((documentSection) => [documentSection, (current[documentSection] ?? 0) + 1])
    ));
    setSentenceSuggestions((current) => ({ ...current, [section]: "" }));
    if (autocompleteEnabled) {
      window.setTimeout(() => void generateSection(section, "", compacted.sections), 0);
    }
  }

  const citedDraftSourceIds = new Set(
    compactDocumentCitations(draftSectionsForReferences, allReferences, sections, "", "", citationStyle).citedSourceIds
  );
  const references = allReferences.filter((reference) => citedDraftSourceIds.has(reference.file_id));

  return (
    <section className="grid min-h-[720px] gap-0 bg-white lg:h-full lg:min-h-0 lg:grid-cols-[300px_minmax(0,1fr)] lg:grid-rows-1">
      {exportOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 p-4">
          <section role="dialog" aria-modal="true" aria-label="Export draft" className="w-full max-w-lg rounded-lg border border-[#cfd7df] bg-white p-5 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold">Export draft</h2>
                <p className="mt-1 text-sm text-[#667386]">Export the current manuscript with its formatting and references.</p>
              </div>
              <button type="button" aria-label="Close export" onClick={() => setExportOpen(false)} className="h-8 w-8 rounded text-xl text-[#667386] hover:bg-[#f1f4f6]">&times;</button>
            </div>
            <div className="mt-5 divide-y divide-[#e1e6eb] border-y border-[#e1e6eb]">
              <button type="button" onClick={exportWordDocument} className="flex w-full items-center justify-between gap-4 py-4 text-left hover:bg-[#f8faf9]">
                <span><strong className="block text-sm">Word document</strong><span className="mt-1 block text-xs text-[#667386]">Downloads an editable Microsoft Word-compatible .doc file.</span></span>
                <span aria-hidden="true" className="text-sm font-semibold text-[#176b5b]">DOC</span>
              </button>
              <button type="button" onClick={exportPdfDocument} className="flex w-full items-center justify-between gap-4 py-4 text-left hover:bg-[#f8faf9]">
                <span><strong className="block text-sm">PDF document</strong><span className="mt-1 block text-xs text-[#667386]">Opens the system print dialog for saving as PDF.</span></span>
                <span aria-hidden="true" className="text-sm font-semibold text-[#a33a2d]">PDF</span>
              </button>
            </div>
            {exportStatus ? <p role="status" className="mt-3 text-sm text-[#176b5b]">{exportStatus}</p> : null}
            <div className="mt-5 flex justify-end">
              <button type="button" onClick={() => setExportOpen(false)} className="rounded border border-[#c5cfda] px-4 py-2 text-sm font-medium">Close</button>
            </div>
          </section>
        </div>
      ) : null}
      {reviewReport ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 p-4">
          <section role="dialog" aria-modal="true" aria-label="Document review" className="w-full max-w-xl rounded-lg border border-[#cfd7df] bg-white p-5 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold">Document review</h2>
                <p className="mt-1 text-sm text-[#667386]">Analysis of the current saved and unsaved draft.</p>
              </div>
              <button type="button" aria-label="Close document review" onClick={() => setReviewReport(null)} className="h-8 w-8 rounded text-xl text-[#667386] hover:bg-[#f1f4f6]">&times;</button>
            </div>
            <dl className="mt-5 grid grid-cols-2 border-y border-[#d7dde6] sm:grid-cols-4">
              <ReviewMetric label="Words" value={reviewReport.wordCount} />
              <ReviewMetric label="Citations" value={reviewReport.citationCount} />
              <ReviewMetric label="Completed" value={reviewReport.completedSections} />
              <ReviewMetric label="Sections" value={reviewReport.totalSections} />
            </dl>
            <h3 className="mt-5 text-sm font-semibold">Review findings</h3>
            {reviewReport.issues.length ? (
              <ul className="mt-2 space-y-2 text-sm text-[#536174]">
                {reviewReport.issues.map((issue) => <li key={issue} className="border-l-2 border-[#d2a84a] pl-3">{issue}</li>)}
              </ul>
            ) : <p className="mt-2 text-sm text-[#176b5b]">No structural issues found in the current draft.</p>}
            <div className="mt-6 flex justify-end">
              <button type="button" onClick={() => setReviewReport(null)} className="rounded bg-[#176b5b] px-4 py-2 text-sm font-semibold text-white">Close</button>
            </div>
          </section>
        </div>
      ) : null}
      <aside className="border-r border-[#d7dde6] bg-[#fbfcfd] p-3 lg:min-h-0 lg:overflow-y-auto">
        <div className="border-b border-[#e1e6eb] p-3 text-sm font-semibold text-[#667386]">
          Document prompt
        </div>
        <div className="p-3">
          <p className="text-xs font-semibold uppercase text-[#667386]">Section prompts</p>
          <div className="mt-3 rounded border border-[#d7dde6] bg-white p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="font-semibold">{activeSection}</p>
              <span className="text-xs text-[#84909d]">Active</span>
            </div>
            <textarea
              aria-label={`${activeSection} prompt`}
              value={sectionPrompts[activeSection]}
              maxLength={5000}
              onChange={(event) => setSectionPrompts((current) => ({ ...current, [activeSection]: event.target.value }))}
              className="mt-2 min-h-24 w-full resize-y rounded border border-transparent p-1 text-sm leading-5 text-[#172026] outline-none hover:border-[#d7dde6] focus:border-[#176b5b]"
            />
            <div className="mt-3 flex gap-2">
            <button
              className="rounded border border-[#c5cfda] px-3 py-1.5 text-sm font-medium hover:bg-[#f5f7f8]"
              type="button"
              onClick={() => setContextOpen(true)}
            >
              Configure context
            </button>
            <button
              className="rounded border border-[#c5cfda] px-3 py-1.5 text-sm font-medium hover:bg-[#f5f7f8] disabled:cursor-wait disabled:opacity-60"
              type="button"
              aria-label={`Generate ${activeSection}`}
              disabled={pendingSection === activeSection}
              onClick={() => void generateSection(activeSection, sentenceSuggestions[activeSection])}
            >
              {pendingSection === activeSection
                ? "Generating..."
                : sentenceSuggestions[activeSection]
                  ? "Regenerate"
                  : generatedSections[activeSection] ? "Continue" : "Generate"}
            </button>
            </div>
            <label className="mt-3 flex items-center justify-between gap-3 text-xs text-[#536174]">
              <span>Citation style</span>
              <select
                aria-label="Citation style"
                value={citationStyle}
                onChange={(event) => onCitationStyleChange(event.target.value as CitationStyle)}
                className="rounded border border-[#c5cfda] bg-white px-2 py-1.5 text-xs text-[#25313d]"
              >
                {citationStyles.map((style) => <option key={style} value={style}>{style}</option>)}
              </select>
            </label>
            <div className="mt-3 border-t border-[#eef2f5] pt-3">
              <FileAttachment onFileSelected={onFileSelected} disabled={isUploadingFile} />
              {attachedFiles.length > 0 ? (
                <div className="mt-2 space-y-1.5">
                  {attachedFiles.map((file) => (
                    <button
                      key={file.id}
                      type="button"
                      title={`Open ${file.filename}`}
                      aria-label={`Open ${file.filename}`}
                      onClick={() => void onOpenFile?.(file.id)}
                      className="block w-full truncate text-left text-xs font-medium text-[#176b5b] underline-offset-2 hover:underline"
                    >
                      {file.filename}
                    </button>
                  ))}
                  <p className="text-xs text-[#667386]">Ready and included in project-source context</p>
                </div>
              ) : null}
              {allReferences.length > 0 ? (
                <div className="mt-2">
                  <button
                    type="button"
                    aria-expanded={sourceListOpen}
                    aria-controls="section-source-list"
                    onClick={() => setSourceListOpen((open) => !open)}
                    className="flex w-full items-center justify-between gap-2 rounded px-1 py-1 text-left text-xs font-medium text-[#176b5b] hover:bg-[#f1f7f5]"
                  >
                    <span>{allReferences.length} verified source{allReferences.length === 1 ? "" : "s"} available</span>
                    <span aria-hidden="true">{sourceListOpen ? "−" : "+"}</span>
                  </button>
                  {sourceListOpen ? (
                    <ol id="section-source-list" aria-label="Available sources" className="mt-2 max-h-56 space-y-2 overflow-y-auto border-t border-[#eef2f5] pt-2 pr-1">
                      {allReferences.map((reference, index) => (
                        <li key={reference.file_id} className="rounded border border-[#d7dde6] bg-white p-2 text-xs">
                          <p className="line-clamp-3 leading-5 text-[#394653]">
                            {formatReference({ ...reference, number: index + 1 }, citationStyle)}
                          </p>
                          {reference.url ? (
                            <a
                              href={reference.url}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-1.5 inline-block font-semibold text-[#176b5b] hover:underline"
                            >
                              View source
                            </a>
                          ) : !reference.file_id.startsWith("literature:") ? (
                            <button
                              type="button"
                              onClick={() => void onOpenFile?.(reference.file_id)}
                              className="mt-1.5 font-semibold text-[#176b5b] hover:underline"
                            >
                              Open file
                            </button>
                          ) : null}
                        </li>
                      ))}
                    </ol>
                  ) : null}
                </div>
              ) : attachedFiles.length === 0 && searchWeb ? (
                <p className="mt-2 text-xs text-[#667386]">External scholarly search enabled</p>
              ) : attachedFiles.length === 0 ? (
                <p className="mt-2 text-xs text-[#a33a2d]">No citation source enabled</p>
              ) : null}
            </div>
          </div>
          {sections.filter((section) => section !== activeSection).map((section) => (
            <button
              key={section}
              type="button"
              onClick={() => {
                snapshotDocument();
                setActiveSection(section);
              }}
              className="flex w-full items-center justify-between border-b border-[#eef2f5] px-2 py-3 text-left text-sm text-[#84909d] hover:text-[#172026]"
            >
              <span>{section}</span><span aria-hidden="true">⌄</span>
            </button>
          ))}
        </div>
      </aside>
      {contextOpen ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/25 p-4">
          <section
            role="dialog"
            aria-modal="true"
            aria-label="Section context configuration"
            className="w-full max-w-md rounded-lg border border-[#d7dde6] bg-white p-5 shadow-xl"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold">Configure context</h2>
                <p className="mt-1 text-sm text-[#667386]">Choose what the Introduction agent can use.</p>
              </div>
              <button type="button" aria-label="Close context configuration" onClick={() => setContextOpen(false)} className="h-8 w-8 rounded hover:bg-[#eef2f5]">×</button>
            </div>
            <div className="mt-5 space-y-3 text-sm">
              <ContextOption label="Current conversation" checked={includeConversation} onChange={setIncludeConversation} />
              <ContextOption label="Project sources" checked={includeProjectSources} onChange={setIncludeProjectSources} />
              <ContextOption label="Search scholarly sources" checked={searchWeb} onChange={setSearchWeb} />
              <ContextOption label="Require citations" checked={requireCitations} onChange={setRequireCitations} />
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button type="button" onClick={() => setContextOpen(false)} className="rounded border border-[#c5cfda] px-3 py-2 text-sm">Cancel</button>
              <button type="button" onClick={() => setContextOpen(false)} className="rounded bg-[#176b5b] px-3 py-2 text-sm font-semibold text-white">Save context</button>
            </div>
          </section>
        </div>
      ) : null}
      <div aria-label="Document canvas" className="px-8 py-10 lg:min-h-0 lg:overflow-y-auto">
      <article
        ref={articleRef}
        className="mx-auto max-w-3xl"
        style={{ fontFamily: documentFont, fontSize: `${documentFontSize}pt` }}
      >
        <h1
          contentEditable
          suppressContentEditableWarning
          aria-label="Document title"
          onBlur={(event) => setTitle(event.currentTarget.textContent?.trim() || "Untitled")}
          className="rounded px-1 text-4xl font-semibold leading-tight text-[#a3a7ad] outline-none focus:bg-[#fbfcfd] focus:ring-1 focus:ring-[#d7dde6]"
        >{title}</h1>
        {isAnalyzing ? <AnalysisSkeleton /> : null}
        <div className="mt-9 space-y-12">
          {sections.map((section, index) => (
            <section key={section} aria-label={`${section} section`} className="group relative min-h-20">
              <h2
                contentEditable
                suppressContentEditableWarning
                aria-label={`${section} heading`}
                onFocus={() => setActiveSection(section)}
                onBlur={(event) => {
                  const heading = event.currentTarget.textContent?.trim() || section;
                  setSectionTitles((current) => ({ ...current, [section]: heading }));
                }}
                className={`rounded px-1 text-xl font-semibold outline-none focus:bg-[#fbfcfd] focus:ring-1 focus:ring-[#d7dde6] ${index === 0 ? "text-[#202124]" : "text-[#a8aaaf]"}`}
              >
                {sectionTitles[section]}
              </h2>
              <div className="mt-4">
                <div
                  key={`${section}-${editorRevisions[section] ?? 0}`}
                  ref={(element) => { sectionEditorRefs.current[section] = element; }}
                  role="textbox"
                  aria-label={`${section} content`}
                  contentEditable
                  suppressContentEditableWarning
                  data-placeholder={generatedSections[section] ? "" : "Start writing or press Generate from the section prompt..."}
                  onFocus={() => setActiveSection(section)}
                  onMouseUp={(event) => rememberEditorSelection(section, event.currentTarget)}
                  onKeyUp={(event) => rememberEditorSelection(section, event.currentTarget)}
                  onSelect={(event) => rememberEditorSelection(section, event.currentTarget)}
                  onClick={(event) => {
                    const image = (event.target as HTMLElement).closest("img") as HTMLImageElement | null;
                    if (image && event.currentTarget.contains(image)) {
                      const alignment = image.closest<HTMLElement>("[data-image-align]")?.dataset.imageAlign;
                      setSelectedImage({
                        section,
                        imageIndex: Array.from(event.currentTarget.querySelectorAll("img")).indexOf(image),
                        alignment: alignment === "center" || alignment === "right" ? alignment : "left"
                      });
                      setSelectedTableCell(null);
                      return;
                    }
                    setSelectedImage(null);
                    const cell = (event.target as HTMLElement).closest("th, td") as HTMLTableCellElement | null;
                    const table = cell?.closest("table") as HTMLTableElement | null;
                    if (!cell || !table || !event.currentTarget.contains(table)) {
                      setSelectedTableCell(null);
                      return;
                    }
                    const tableIndex = Array.from(event.currentTarget.querySelectorAll("table")).indexOf(table);
                    setSelectedTableCell({
                      section,
                      tableIndex,
                      rowIndex: cell.parentElement instanceof HTMLTableRowElement ? cell.parentElement.rowIndex : 0,
                      columnIndex: cell.cellIndex
                    });
                  }}
                  onInput={(event) => {
                    const content = editorContentToMarkdown(event.currentTarget);
                    updateSectionContent(section, content, false);
                    setDraftSectionsForReferences((current) => ({ ...current, [section]: content }));
                    rememberEditorSelection(section, event.currentTarget);
                  }}
                  onBlur={(event) => {
                    rememberEditorSelection(section, event.currentTarget);
                    const nextFocus = event.relatedTarget as HTMLElement | null;
                    if (nextFocus?.closest('[aria-label="Editor toolbar"], [role="dialog"]')) return;
                    const content = editorContentToMarkdown(event.currentTarget);
                    event.currentTarget.replaceChildren();
                    updateSectionContent(section, content, true);
                    setEditorRevisions((current) => ({ ...current, [section]: (current[section] ?? 0) + 1 }));
                  }}
                  className="min-h-16 rounded px-1 leading-[1.7] text-[#202124] outline-none before:pointer-events-none before:text-sm before:text-[#a3a7ad] before:content-[attr(data-placeholder)] focus:bg-[#fbfcfd] focus:ring-1 focus:ring-[#d7dde6] focus:before:content-none"
                >
                  {generatedSections[section] ? <MarkdownContent content={generatedSections[section]} /> : null}
                </div>
                {selectedTableCell?.section === section ? (
                  <div role="toolbar" aria-label="Table tools" className="mt-2 flex flex-wrap items-center gap-1 rounded border border-[#cfd7df] bg-[#f8faf9] p-1.5 text-xs shadow-sm">
                    <span className="px-2 font-semibold text-[#394653]">Table</span>
                    <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => editSelectedTable("row-above")} className="rounded px-2 py-1.5 hover:bg-white">Insert row above</button>
                    <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => editSelectedTable("row-below")} className="rounded px-2 py-1.5 hover:bg-white">Insert row below</button>
                    <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => editSelectedTable("column-left")} className="rounded px-2 py-1.5 hover:bg-white">Insert column left</button>
                    <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => editSelectedTable("column-right")} className="rounded px-2 py-1.5 hover:bg-white">Insert column right</button>
                    <span aria-hidden="true" className="mx-1 h-5 w-px bg-[#cfd7df]" />
                    <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => editSelectedTable("delete-row")} className="rounded px-2 py-1.5 text-[#a33a2d] hover:bg-white">Delete row</button>
                    <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => editSelectedTable("delete-column")} className="rounded px-2 py-1.5 text-[#a33a2d] hover:bg-white">Delete column</button>
                    <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => editSelectedTable("delete-table")} className="rounded px-2 py-1.5 text-[#a33a2d] hover:bg-white">Delete table</button>
                  </div>
                ) : null}
                {selectedImage?.section === section ? (
                  <div role="toolbar" aria-label="Image alignment" className="mt-2 flex items-center gap-1 rounded border border-[#cfd7df] bg-[#f8faf9] p-1.5 text-xs shadow-sm">
                    <span className="px-2 font-semibold text-[#394653]">Image</span>
                    {(["left", "center", "right"] as ImageAlignment[]).map((alignment) => (
                      <button
                        key={alignment}
                        type="button"
                        aria-label={`Align image ${alignment}`}
                        aria-pressed={selectedImage.alignment === alignment}
                        onMouseDown={(event) => event.preventDefault()}
                        onClick={() => alignSelectedImage(alignment)}
                        className={`rounded px-3 py-1.5 capitalize ${selectedImage.alignment === alignment ? "bg-[#dceee8] text-[#176b5b]" : "hover:bg-white"}`}
                      >
                        {alignment}
                      </button>
                    ))}
                  </div>
                ) : null}
                {generatedSections[section] && !sentenceSuggestions[section] ? <button
                  type="button"
                  aria-label={`Continue ${section}`}
                  disabled={pendingSection === section}
                  onClick={() => void generateSection(section)}
                  className="mt-2 rounded border border-[#c5cfda] bg-white px-3 py-1.5 text-sm font-medium text-[#176b5b] shadow-sm hover:bg-[#f5f7f8] disabled:cursor-wait disabled:opacity-60"
                >
                  {pendingSection === section ? "Generating..." : "Continue writing"}
                </button> : null}
              </div>
              {sentenceSuggestions[section] ? (
                <div
                  className="mt-3 rounded border border-[#b8d7cf] bg-[#f3faf7] p-3"
                  role="status"
                  aria-label={`${section} sentence suggestion`}
                >
                  <p className="text-base leading-7 text-[#202124]">{sentenceSuggestions[section]}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button type="button" onClick={() => acceptSuggestion(section)} className="rounded bg-[#176b5b] px-3 py-1.5 text-sm font-semibold text-white">Accept</button>
                    <button type="button" onClick={() => void generateSection(section, sentenceSuggestions[section])} disabled={pendingSection === section} className="rounded border border-[#c5cfda] bg-white px-3 py-1.5 text-sm font-medium disabled:opacity-60">Regenerate</button>
                    <button type="button" onClick={() => setSentenceSuggestions((current) => ({ ...current, [section]: "" }))} className="rounded px-3 py-1.5 text-sm text-[#667386] hover:bg-white">Dismiss</button>
                  </div>
                </div>
              ) : null}
              {suggestionError[section] ? <p role="alert" className="mt-2 text-sm text-[#a33a2d]">{suggestionError[section]}</p> : null}
            </section>
          ))}
          <section aria-label="References section" className="min-h-20 border-t border-[#edf1f5] pt-8">
            <h2 contentEditable suppressContentEditableWarning className="rounded px-1 text-xl font-semibold text-[#a8aaaf] outline-none focus:ring-1 focus:ring-[#d7dde6]">References</h2>
            {references.length ? (
              <div className="mt-4 space-y-2 leading-[1.7] text-[#4b5563]">
                {references.map((reference) => (
                  <p key={reference.file_id}>
                    {reference.url ? (
                      <a href={reference.url} target="_blank" rel="noreferrer" className="hover:underline">
                        {formatReference(reference, citationStyle)}
                      </a>
                    ) : formatReference(reference, citationStyle)}
                  </p>
                ))}
              </div>
            ) : <p className="mt-3 text-sm text-[#a3a7ad]">Verified citations used in generated sections will appear here.</p>}
          </section>
        </div>
      </article>
      </div>
    </section>
  );
}

function AnalysisSkeleton() {
  return (
    <div role="status" className="mt-6" aria-label="Analyzing document prompt">
      <p className="text-sm text-[#737780]">Analyzing your topic...</p>
      <div className="mt-5 space-y-3 animate-pulse">
        {["w-3/4", "w-1/2", "w-2/3"].map((width) => <div key={width} className={`h-4 rounded bg-[#f0f1f3] ${width}`} />)}
      </div>
    </div>
  );
}

function ReviewMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="px-3 py-4 text-center">
      <dt className="text-xs font-medium uppercase text-[#738092]">{label}</dt>
      <dd className="mt-1 text-xl font-semibold text-[#202124]">{value}</dd>
    </div>
  );
}

function createDocumentReview(documentSections: Record<string, string>, sections: string[]): DocumentReview {
  const completedSections = sections.filter((section) => documentSections[section]?.trim()).length;
  const manuscript = sections.map((section) => documentSections[section] ?? "").join("\n");
  const readableText = manuscript
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/<[^>]+>/g, " ")
    .replace(/[#*_~|`$]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const wordCount = readableText ? readableText.split(/\s+/).length : 0;
  const ieeeCitations = manuscript.match(/\[(?:\d+(?:\s*[-,]\s*\d+)*)\]/g) ?? [];
  const authorDateCitations = manuscript.match(/\([^)]*\b(?:19|20)\d{2}[a-z]?[^)]*\)/g) ?? [];
  const citationCount = ieeeCitations.length + authorDateCitations.length;
  const emptySections = sections.filter((section) => !documentSections[section]?.trim());
  const sentences = readableText
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.toLowerCase().replace(/[^a-z0-9\s]/g, "").replace(/\s+/g, " ").trim())
    .filter((sentence) => sentence.split(" ").length >= 8);
  const hasRepeatedSentence = new Set(sentences).size < sentences.length;
  const issues: string[] = [];

  if (emptySections.length) issues.push(`Empty sections: ${emptySections.join(", ")}.`);
  if (wordCount > 0 && wordCount < 300) issues.push("The draft is brief; develop the argument and evidence before final review.");
  if (wordCount > 0 && citationCount === 0) issues.push("No in-text citations were detected in the draft.");
  if (hasRepeatedSentence) issues.push("At least one full sentence is repeated in the document.");

  return { wordCount, citationCount, completedSections, totalSections: sections.length, issues };
}

function buildExportHtml(title: string, manuscript: string, font: string, fontSize: number) {
  const safeTitle = title.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[character] ?? character);
  const safeFont = font.replace(/[^a-zA-Z0-9 ,'-]/g, "") || "Times New Roman";
  const safeSize = Math.max(8, Math.min(32, fontSize));
  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>${safeTitle}</title>
  <style>
    @page { size: A4; margin: 22mm 20mm; }
    body { margin: 0 auto; max-width: 170mm; color: #202124; font-family: "${safeFont}", serif; font-size: ${safeSize}pt; line-height: 1.7; }
    h1 { margin: 0 0 24pt; font-size: 24pt; line-height: 1.2; }
    h2 { margin: 24pt 0 10pt; font-size: 16pt; page-break-after: avoid; }
    h3 { margin: 18pt 0 8pt; font-size: 13pt; page-break-after: avoid; }
    p { margin: 0 0 9pt; }
    a { color: inherit; text-decoration: none; }
    table { width: 100%; border-collapse: collapse; margin: 12pt 0; page-break-inside: avoid; }
    th, td { border: 1px solid #9ca3af; padding: 6pt; vertical-align: top; }
    th { background: #f1f3f5; font-weight: 700; }
    img { max-width: 100%; max-height: 220mm; object-fit: contain; }
    [data-image-align] { display: flex; width: 100%; margin: 12pt 0; }
    [data-image-align="left"] { justify-content: flex-start; }
    [data-image-align="center"] { justify-content: center; }
    [data-image-align="right"] { justify-content: flex-end; }
    @media print { body { max-width: none; } }
  </style>
</head>
<body>${manuscript}</body>
</html>`;
}

function exportFilename(title: string) {
  return title
    .trim()
    .replace(/[^a-zA-Z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "research-draft";
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function activeEditorRange(editor: HTMLElement) {
  const selection = window.getSelection();
  if (selection?.rangeCount) {
    const range = selection.getRangeAt(0);
    if (editor.contains(range.commonAncestorContainer)) return range;
  }
  const range = document.createRange();
  range.selectNodeContents(editor);
  range.collapse(false);
  return range;
}

function clampTableDimension(value: string, maximum = 20) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) return 1;
  return Math.max(1, Math.min(maximum, parsed));
}

function insertTableAtSelection(editor: HTMLElement, rowCount: number, columnCount: number) {
  const rows = clampTableDimension(String(rowCount));
  const columns = clampTableDimension(String(columnCount), 12);
  const range = activeEditorRange(editor);
  let insertionAnchor: Node | null = range.startContainer;

  while (insertionAnchor.parentNode && insertionAnchor.parentNode !== editor) {
    insertionAnchor = insertionAnchor.parentNode;
  }

  const table = document.createElement("table");
  const tableHead = document.createElement("thead");
  const headingRow = document.createElement("tr");
  for (let column = 0; column < columns; column += 1) {
    const heading = document.createElement("th");
    heading.textContent = `Column ${column + 1}`;
    headingRow.append(heading);
  }
  tableHead.append(headingRow);
  table.append(tableHead);

  const tableBody = document.createElement("tbody");
  for (let row = 1; row < rows; row += 1) {
    const bodyRow = document.createElement("tr");
    for (let column = 0; column < columns; column += 1) {
      const cell = document.createElement("td");
      cell.textContent = "New cell";
      bodyRow.append(cell);
    }
    tableBody.append(bodyRow);
  }
  table.append(tableBody);

  const tableContainer = document.createElement("div");
  tableContainer.append(table);
  const trailingParagraph = document.createElement("p");
  trailingParagraph.dataset.tableTrailingParagraph = "true";
  trailingParagraph.setAttribute("aria-label", "Paragraph after table");
  trailingParagraph.append(document.createElement("br"));

  const fragment = document.createDocumentFragment();
  fragment.append(tableContainer, trailingParagraph);
  if (insertionAnchor.parentNode === editor) {
    editor.insertBefore(fragment, insertionAnchor.nextSibling);
  } else {
    editor.append(fragment);
  }

  const nextRange = document.createRange();
  nextRange.selectNodeContents(trailingParagraph);
  nextRange.collapse(true);
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(nextRange);
  editor.focus();
}

function editMarkdownTable(
  content: string,
  selection: SelectedTableCell,
  action: "row-above" | "row-below" | "column-left" | "column-right" | "delete-row" | "delete-column" | "delete-table"
) {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  let currentTable = -1;

  for (let start = 0; start < lines.length - 1; start += 1) {
    if (!/^\s*\|.*\|\s*$/.test(lines[start]) || !/^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$/.test(lines[start + 1])) continue;
    currentTable += 1;
    let end = start + 2;
    while (end < lines.length && /^\s*\|.*\|\s*$/.test(lines[end])) end += 1;
    if (currentTable !== selection.tableIndex) {
      start = end - 1;
      continue;
    }

    const rows = [parseMarkdownTableRow(lines[start]), ...lines.slice(start + 2, end).map(parseMarkdownTableRow)];
    const columnCount = rows[0]?.length ?? 0;
    if (!rows.length || !columnCount) return null;
    let nextRow = Math.max(0, Math.min(selection.rowIndex, rows.length - 1));
    let nextColumn = Math.max(0, Math.min(selection.columnIndex, columnCount - 1));

    if (action === "delete-table" || (action === "delete-row" && rows.length === 1) || (action === "delete-column" && columnCount === 1)) {
      lines.splice(start, end - start);
      return { content: lines.join("\n").replace(/\n{3,}/g, "\n\n").trim(), selection: null };
    }
    if (action === "row-above" || action === "row-below") {
      const newRow = Array.from({ length: columnCount }, () => "New cell");
      const insertionIndex = action === "row-above" && nextRow > 0 ? nextRow : nextRow + 1;
      rows.splice(insertionIndex, 0, newRow);
      nextRow = insertionIndex;
    } else if (action === "column-left" || action === "column-right") {
      const insertionIndex = action === "column-left" ? nextColumn : nextColumn + 1;
      rows.forEach((row, rowIndex) => row.splice(insertionIndex, 0, rowIndex === 0 ? "Column" : "New cell"));
      nextColumn = insertionIndex;
    } else if (action === "delete-row") {
      rows.splice(nextRow, 1);
      nextRow = Math.min(nextRow, rows.length - 1);
    } else if (action === "delete-column") {
      rows.forEach((row) => row.splice(nextColumn, 1));
      nextColumn = Math.min(nextColumn, rows[0].length - 1);
    }

    const tableLines = [
      markdownTableRow(rows[0]),
      markdownTableRow(rows[0].map(() => "---")),
      ...rows.slice(1).map(markdownTableRow)
    ];
    lines.splice(start, end - start, ...tableLines);
    return {
      content: lines.join("\n").replace(/\n{3,}/g, "\n\n").trim(),
      selection: { ...selection, rowIndex: nextRow, columnIndex: nextColumn }
    };
  }
  return null;
}

function parseMarkdownTableRow(line: string) {
  return line.trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
}

function markdownTableRow(cells: string[]) {
  return `| ${cells.join(" | ")} |`;
}

function replaceEditorRange(editor: HTMLElement, replacement: string, selectionStart: number, selectionLength: number) {
  const range = activeEditorRange(editor);
  range.deleteContents();
  const node = document.createTextNode(replacement);
  range.insertNode(node);

  const selection = window.getSelection();
  const nextRange = document.createRange();
  nextRange.setStart(node, Math.min(selectionStart, node.length));
  nextRange.setEnd(node, Math.min(selectionStart + selectionLength, node.length));
  selection?.removeAllRanges();
  selection?.addRange(nextRange);
  editor.focus();
  editor.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: replacement }));
}

function insertMarkdownAtSelection(editor: HTMLElement, markdown: string) {
  const selected = activeEditorRange(editor).toString();
  replaceEditorRange(editor, markdown, markdown.length, selected ? 0 : 0);
}

function wrapSelectionWithMarkdown(editor: HTMLElement, prefix: string, suffix: string, placeholder: string) {
  const selected = activeEditorRange(editor).toString() || placeholder;
  const replacement = `${prefix}${selected}${suffix}`;
  replaceEditorRange(editor, replacement, prefix.length, selected.length);
}

function toggleSelectionFormat(editor: HTMLElement, command: string, tagName: "strong" | "em" | "u" | "s") {
  const range = activeEditorRange(editor);
  if (range.collapsed || !range.toString()) return;

  if (typeof document.execCommand === "function") {
    editor.focus();
    document.execCommand(command, false);
    return;
  }

  const startElement = range.startContainer instanceof HTMLElement
    ? range.startContainer
    : range.startContainer.parentElement;
  const endElement = range.endContainer instanceof HTMLElement
    ? range.endContainer
    : range.endContainer.parentElement;
  const formattedAncestor = startElement?.closest(tagName);
  if (formattedAncestor && formattedAncestor === endElement?.closest(tagName) && formattedAncestor.textContent === range.toString()) {
    formattedAncestor.replaceWith(...Array.from(formattedAncestor.childNodes));
    return;
  }

  const wrapper = document.createElement(tagName);
  wrapper.append(range.extractContents());
  range.insertNode(wrapper);
  range.selectNodeContents(wrapper);
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);
}

function applyStyleToSelection(editor: HTMLElement, property: "fontFamily" | "fontSize", value: string) {
  const range = activeEditorRange(editor);
  if (range.collapsed || !range.toString()) return;
  const selectedText = range.toString().trim();
  const matchingStyledSpan = Array.from(editor.querySelectorAll("span")).find((span) => (
    range.intersectsNode(span) && span.textContent?.trim() === selectedText
  ));
  if (matchingStyledSpan) {
    matchingStyledSpan.style[property] = value;
    return;
  }
  const startElement = range.startContainer instanceof HTMLElement
    ? range.startContainer
    : range.startContainer.parentElement;
  const endElement = range.endContainer instanceof HTMLElement
    ? range.endContainer
    : range.endContainer.parentElement;
  const styledAncestor = startElement?.closest("span");
  if (
    styledAncestor
    && styledAncestor === endElement?.closest("span")
    && styledAncestor.textContent?.trim() === selectedText
  ) {
    styledAncestor.style[property] = value;
    return;
  }
  const wrapper = document.createElement("span");
  wrapper.style[property] = value;
  wrapper.append(range.extractContents());
  range.insertNode(wrapper);
  range.selectNodeContents(wrapper);
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);
}

function formatSelectedBlocks(editor: HTMLElement, headingPrefix: string) {
  const range = activeEditorRange(editor);
  if (range.collapsed || !range.toString()) return;
  if (typeof document.execCommand === "function") {
    const block = headingPrefix ? `h${headingPrefix.trim().length}` : "p";
    editor.focus();
    document.execCommand("formatBlock", false, block);
    return;
  }
  prefixSelectionLines(editor, headingPrefix);
}

function prefixSelectionLines(editor: HTMLElement, prefix: string) {
  const selected = activeEditorRange(editor).toString();
  const source = selected || (prefix ? "Heading" : "Paragraph");
  const replacement = source
    .split("\n")
    .map((line) => `${prefix}${line.replace(/^#{1,3}\s+/, "")}`)
    .join("\n");
  replaceEditorRange(editor, replacement, prefix.length, Math.max(replacement.length - prefix.length, 0));
}

function editorContentToMarkdown(editor: HTMLElement) {
  const serialize = (node: Node): string => {
    if (node.nodeType === Node.TEXT_NODE) return node.textContent ?? "";
    if (!(node instanceof HTMLElement)) return "";
    const children = () => Array.from(node.childNodes).map(serialize).join("");
    const tag = node.tagName.toLowerCase();

    if (tag === "br") return "\n";
    if (tag === "strong" || tag === "b") return `**${children()}**`;
    if (tag === "em" || tag === "i") return `*${children()}*`;
    if (tag === "u") return `<u>${children()}</u>`;
    if (tag === "s" || tag === "strike" || tag === "del") return `~~${children()}~~`;
    if (tag === "code" && node.parentElement?.tagName.toLowerCase() !== "pre") return `\`${children()}\``;
    if (tag === "pre") return `\n\`\`\`\n${node.textContent ?? ""}\n\`\`\`\n`;
    if (/^h[1-6]$/.test(tag)) return `${"#".repeat(Number(tag[1]))} ${children()}\n\n`;
    if (tag === "p") return `${children()}\n\n`;
    if (tag === "li") return children();
    if (tag === "ul") return `${Array.from(node.children).map((child) => `- ${serialize(child)}`).join("\n")}\n\n`;
    if (tag === "ol") return `${Array.from(node.children).map((child, index) => `${index + 1}. ${serialize(child)}`).join("\n")}\n\n`;
    if (tag === "img") return `![${node.getAttribute("alt") ?? "Image"}](${node.getAttribute("src") ?? ""})`;
    if (tag === "a") return `[${children()}](${node.getAttribute("href") ?? ""})`;
    if (tag === "span" && node.dataset.imageAlign) {
      const alignment = node.dataset.imageAlign === "center" || node.dataset.imageAlign === "right"
        ? node.dataset.imageAlign
        : "left";
      return `<span data-image-align="${alignment}">${children()}</span>`;
    }
    if (tag === "span" && (node.style.fontFamily || node.style.fontSize)) {
      const meaningfulChildren = Array.from(node.childNodes).filter((child) => (
        child.nodeType !== Node.TEXT_NODE || Boolean(child.textContent?.trim())
      ));
      const nestedStyle = meaningfulChildren.length === 1
        && meaningfulChildren[0] instanceof HTMLElement
        && meaningfulChildren[0].tagName.toLowerCase() === "span"
        ? meaningfulChildren[0]
        : null;
      const font = (node.style.fontFamily || nestedStyle?.style.fontFamily || "").replace(/["']/g, "");
      const size = node.style.fontSize || nestedStyle?.style.fontSize || "";
      const attributes = `${font ? ` data-font="${font}"` : ""}${size ? ` data-size="${size}"` : ""}`;
      const content = nestedStyle
        ? Array.from(nestedStyle.childNodes).map(serialize).join("")
        : children();
      return `<span${attributes}>${content}</span>`;
    }
    if (tag === "table") {
      const rows = Array.from(node.querySelectorAll("tr")).map((row) =>
        Array.from(row.querySelectorAll("th, td")).map((cell) => cell.textContent?.trim() ?? "")
      );
      if (!rows.length) return "";
      const header = `| ${rows[0].join(" | ")} |`;
      const divider = `| ${rows[0].map(() => "---").join(" | ")} |`;
      return `\n\n${[header, divider, ...rows.slice(1).map((row) => `| ${row.join(" | ")} |`)].join("\n")}\n\n`;
    }
    return children();
  };

  return Array.from(editor.childNodes)
    .map(serialize)
    .join("")
    .replace(/\u00a0/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function ContextOption({
  label,
  checked,
  onChange
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-4 rounded border border-[#e1e6eb] px-3 py-3">
      <span>{label}</span>
      <input
        type="checkbox"
        aria-label={label}
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="h-4 w-4 accent-[#176b5b]"
      />
    </label>
  );
}

function documentTitle(prompt: string) {
  const trimmed = prompt.trim();
  if (!trimmed) return "Untitled";
  if (/\bRAG\b|retrieval[ -]augmented generation/i.test(trimmed)) {
    return "Retrieval-Augmented Generation: Principles, Architecture, and Applications";
  }
  if (/\bAI agents?\b/i.test(trimmed)) {
    return "AI Agents: Architectures, Capabilities, and Evaluation";
  }
  return trimmed.charAt(0).toUpperCase() + trimmed.slice(1).replace(/\?$/, "");
}

function defaultSectionPrompt(section: string, prompt: string) {
  const topic = documentTitle(prompt);
  const prompts: Record<string, string> = {
    Introduction: `- Define the research problem and motivation\n- Establish the scope and objectives for ${topic}`,
    "Literature Review": "- Synthesize the most relevant prior work\n- Compare findings and identify unresolved gaps",
    Methodology: "- Describe the proposed methods, data, and evaluation design\n- State assumptions and reproducibility requirements",
    Results: "- Present findings without overstating the evidence\n- Report quantitative outcomes and uncertainty",
    Discussion: "- Interpret findings against prior work\n- Explain limitations, implications, and alternative explanations",
    Conclusion: "- Summarize the supported contribution\n- State practical next steps and future research"
  };
  return prompts[section];
}

function extractCitationNumbers(content: string) {
  const matches = [...content.matchAll(/\[(\d+)(?:,\s*p{1,2}\.\s*[^\]]+)?\]/g)];
  return [...new Set(matches.map((match) => Number(match[1])))];
}

function combineReferences(
  projectReferences: FileReference[],
  discoveredReferences: FileReference[]
) {
  const unique = new Map<string, FileReference>();
  for (const reference of [...projectReferences, ...discoveredReferences]) {
    if (!unique.has(reference.file_id)) unique.set(reference.file_id, reference);
  }
  return [...unique.values()].map((reference, index) => {
    const number = index + 1;
    return {
      ...reference,
      number,
      citation: reference.citation.replace(/^\[\d+\]/, `[${number}]`)
    };
  });
}

function orderReferenceCatalog(references: FileReference[], referenceOrder: string[]) {
  const position = new Map(referenceOrder.map((sourceId, index) => [sourceId, index]));
  return [...references]
    .sort((left, right) => {
      const leftPosition = position.get(left.file_id) ?? Number.MAX_SAFE_INTEGER;
      const rightPosition = position.get(right.file_id) ?? Number.MAX_SAFE_INTEGER;
      return leftPosition - rightPosition || left.number - right.number;
    })
    .map((reference, index) => ({
      ...reference,
      number: index + 1,
      citation: reference.citation.replace(/^\[\d+\]/, `[${index + 1}]`)
    }));
}

function compactDocumentCitations(
  documentSections: Record<string, string>,
  references: FileReference[],
  sectionSequence: string[],
  pendingSection = "",
  pendingContent = "",
  citationStyle: CitationStyle = "IEEE"
) {
  const referenceByNumber = new Map(references.map((reference) => [reference.number, reference]));
  const citedSourceIds: string[] = [];
  const collect = (content: string) => {
    if (citationStyle !== "IEEE") {
      const matches = references
        .map((reference) => ({ reference, index: content.indexOf(citationMarker(reference, citationStyle)) }))
        .filter(({ index }) => index >= 0)
        .sort((left, right) => left.index - right.index);
      for (const { reference } of matches) {
        if (!citedSourceIds.includes(reference.file_id)) citedSourceIds.push(reference.file_id);
      }
      return;
    }
    for (const number of extractCitationNumbers(content)) {
      const sourceId = referenceByNumber.get(number)?.file_id;
      if (sourceId && !citedSourceIds.includes(sourceId)) citedSourceIds.push(sourceId);
    }
  };
  for (const section of sectionSequence) {
    collect(documentSections[section] ?? "");
    if (section === pendingSection) collect(pendingContent);
  }
  const referenceOrder = [
    ...citedSourceIds,
    ...references.map((reference) => reference.file_id).filter((sourceId) => !citedSourceIds.includes(sourceId))
  ];
  const manuscriptNumber = new Map(referenceOrder.map((sourceId, index) => [sourceId, index + 1]));
  const remap = (content: string) => citationStyle === "IEEE" ? content.replace(
    /\[(\d+)(?:\s*,\s*p{1,2}\.\s*[^\]]+)?\]/gi,
    (match, value: string) => {
      const sourceId = referenceByNumber.get(Number(value))?.file_id;
      const number = sourceId ? manuscriptNumber.get(sourceId) : undefined;
      return number ? `[${number}]` : match;
    }
  ) : content;
  return {
    sections: Object.fromEntries(
      Object.entries(documentSections).map(([section, content]) => [section, remap(content)])
    ),
    pendingContent: remap(pendingContent),
    referenceOrder,
    citedSourceIds
  };
}

function sameStringArray(left: string[], right: string[]) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function buildScholarlyContext(references: FileReference[], citationStyle: CitationStyle) {
  const sources = references.filter((reference) => reference.evidence?.trim());
  if (sources.length === 0) return "";
  return "\n\nVERIFIED SCHOLARLY SOURCES (cite only these source numbers):\n" + sources
    .map((reference) => (
      `${formatReference(reference, citationStyle)}\n` +
      `INLINE CITATION: ${citationMarker(reference, citationStyle)}\n` +
      `EVIDENCE: ${reference.evidence}`
    ))
    .join("\n\n");
}

function firstCompleteSentence(content: string) {
  const text = normalizeIeeeCitationPlacement(
    content.trim().replace(/^#{1,6}\s+[^\n]+\n+/, "").replace(/\s+/g, " ")
  );
  if (!text) return "";
  let bracketDepth = 0;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (character === "[") bracketDepth += 1;
    if (character === "]") bracketDepth = Math.max(0, bracketDepth - 1);
    if (bracketDepth > 0 || !".!?".includes(character)) continue;
    const previous = text[index - 1] ?? "";
    const next = text[index + 1] ?? "";
    if (character === "." && /\d/.test(previous) && /\d/.test(next)) continue;
    if (character === "." && /\b(?:e\.g|i\.e|et al|fig|dr|mr|mrs|ms|prof|p)$/i.test(text.slice(0, index))) continue;
    if (!next || /\s/.test(next)) return text.slice(0, index + 1).trim();
  }
  return text;
}

function normalizeIeeeCitationPlacement(content: string) {
  return content.replace(
    /([.!?])\s*(\[\d+(?:\s*,\s*p{1,2}\.\s*[^\]]+)?\])(?=\s|$)/g,
    " $2$1"
  );
}

function hasVerifiedCitation(sentence: string, references: FileReference[], citationStyle: CitationStyle) {
  if (citationStyle !== "IEEE") {
    return references.some((reference) => sentence.includes(citationMarker(reference, citationStyle)));
  }
  const validNumbers = new Set(references.map((reference) => reference.number));
  return extractCitationNumbers(sentence).some((number) => validNumbers.has(number));
}

function attachBestEvidenceCitation(
  sentence: string,
  references: FileReference[],
  citationStyle: CitationStyle
) {
  const claim = sentence.trim();
  const claimTerms = meaningfulTerms(claim);
  if (!claim || claimTerms.size === 0) return sentence;

  let bestReference: FileReference | undefined;
  let bestOverlap = 0;
  let bestScore = 0;
  for (const reference of references) {
    if (!reference.evidence?.trim()) continue;
    const evidenceTerms = meaningfulTerms(`${reference.filename} ${reference.evidence}`);
    const overlap = [...claimTerms].filter((term) => evidenceTerms.has(term)).length;
    const score = overlap / claimTerms.size;
    if (overlap > bestOverlap || (overlap === bestOverlap && score > bestScore)) {
      bestReference = reference;
      bestOverlap = overlap;
      bestScore = score;
    }
  }

  if (!bestReference || bestOverlap < 2 || bestScore < 0.12) return sentence;
  const punctuation = claim.match(/[.!?]$/)?.[0] ?? ".";
  const text = /[.!?]$/.test(claim) ? claim.slice(0, -1).trimEnd() : claim;
  return `${text} ${citationMarker(bestReference, citationStyle)}${punctuation}`;
}

function normalizeVerifiedCitations(
  content: string,
  references: FileReference[],
  citationStyle: CitationStyle
) {
  const validNumbers = new Set(references.map((reference) => reference.number));
  let styledContent = content;
  for (const reference of references) {
    const targetMarker = citationMarker(reference, citationStyle);
    for (const style of citationStyles) {
      const existingMarker = citationMarker(reference, style);
      if (existingMarker !== targetMarker) {
        styledContent = styledContent.replaceAll(existingMarker, targetMarker);
      }
    }
  }
  const normalized = styledContent
    .replace(/\s*\[(\d+)(?:\s*,\s*p{1,2}\.\s*[^\]]+)?\]/gi, (_match, value: string) => {
      const number = Number(value);
      const reference = references.find((item) => item.number === number);
      return validNumbers.has(number) && reference ? ` ${citationMarker(reference, citationStyle)}` : "";
    })
    .replace(/\s*\[(?:source|ref(?:erence)?):[^\]]+\]/gi, "")
    .replace(/\s+([,.;!?])/g, "$1")
    .replace(/[\t ]{2,}/g, " ")
    .trim();
  return repairGeneratedTableMarkdown(normalized);
}

function repairGeneratedTableMarkdown(content: string) {
  if (!/\|\s*:?-{3,}:?\s*\|/.test(content)) return content;
  return content
    .replace(/([^\n])[\t ]+(?=\|\s*Column\s+1\s*\|)/gi, "$1\n")
    .replace(/\|[\t ]+\|(?=[\t ]*(?:Column\s+\d+|:?-{3,}:?|New cell)[\t ]*\|)/gi, "|\n|");
}

function nextRhetoricalMove(section: string, content: string) {
  const sentenceCount = (content.match(/[^.!?]+[.!?]+/g) ?? []).length;
  const moves: Record<string, string[]> = {
    Introduction: [
      "Define the specific research problem and its setting.",
      "Explain why the problem matters and what consequences remain unresolved.",
      "Identify the limitation or evidence gap in current approaches.",
      "State the study objective and the proposed contribution.",
      "Clarify the scope, assumptions, or research questions."
    ],
    "Literature Review": [
      "Introduce the most relevant research stream.",
      "Compare methods or findings across prior studies.",
      "Explain a disagreement, limitation, or missing capability in prior work.",
      "Synthesize the unresolved gap that motivates this study."
    ],
    Methodology: [
      "Describe the research design and why it fits the objective.",
      "Specify the data, participants, materials, or experimental setting.",
      "Explain the procedure, model, or analysis pipeline.",
      "Define evaluation metrics, baselines, and reproducibility controls."
    ],
    Results: [
      "Report the primary result with its measurement or comparison.",
      "Report a complementary result, uncertainty estimate, or robustness check.",
      "Contrast the result with the strongest baseline or prior finding.",
      "Summarize the result without interpreting beyond the evidence."
    ],
    Discussion: [
      "Interpret the principal finding in relation to the research objective.",
      "Compare the interpretation with prior literature.",
      "Explain limitations and plausible alternative explanations.",
      "State practical or theoretical implications without overstating them."
    ],
    Conclusion: [
      "Summarize the evidence-supported contribution.",
      "State the main limitation or boundary of the conclusion.",
      "Give a concrete implication or future research direction."
    ]
  };
  const sectionMoves = moves[section] ?? ["Add a new evidence-supported point that advances the section."];
  return sectionMoves[Math.min(sentenceCount, sectionMoves.length - 1)];
}

function isNearDuplicate(candidate: string, existingContent: string) {
  if (!existingContent.trim()) return false;
  const candidateTerms = meaningfulTerms(candidate);
  if (candidateTerms.size === 0) return false;
  const candidateTokens = comparisonTokens(candidate);
  const existingSentences = existingContent.match(/[^.!?]+[.!?]?/g) ?? [existingContent];
  return existingSentences.some((sentence) => {
    const existingTerms = meaningfulTerms(sentence);
    const overlap = [...candidateTerms].filter((term) => existingTerms.has(term)).length;
    const union = new Set([...candidateTerms, ...existingTerms]).size;
    const smallerSet = Math.min(candidateTerms.size, existingTerms.size);
    const novelTermRatio = (candidateTerms.size - overlap) / candidateTerms.size;
    const sharedPhraseLength = longestSharedTokenRun(candidateTokens, comparisonTokens(sentence));
    return (
      (union > 0 && overlap / union >= 0.72) ||
      (smallerSet > 0 && overlap / smallerSet >= 0.78) ||
      (candidateTerms.size >= 8 && novelTermRatio < 0.3) ||
      sharedPhraseLength >= 6
    );
  });
}

function isSameSentence(left: string, right: string) {
  return comparisonTokens(left).join(" ") === comparisonTokens(right).join(" ");
}

function comparisonTokens(content: string) {
  return content
    .toLowerCase()
    .replace(/\[\d+\]/g, "")
    .match(/[a-z0-9]+/g) ?? [];
}

function longestSharedTokenRun(left: string[], right: string[]) {
  if (left.length === 0 || right.length === 0) return 0;
  const previous = new Array<number>(right.length + 1).fill(0);
  let longest = 0;
  for (let leftIndex = 1; leftIndex <= left.length; leftIndex += 1) {
    const current = new Array<number>(right.length + 1).fill(0);
    for (let rightIndex = 1; rightIndex <= right.length; rightIndex += 1) {
      if (left[leftIndex - 1] === right[rightIndex - 1]) {
        current[rightIndex] = previous[rightIndex - 1] + 1;
        longest = Math.max(longest, current[rightIndex]);
      }
    }
    for (let index = 0; index < current.length; index += 1) previous[index] = current[index];
  }
  return longest;
}

function meaningfulTerms(content: string) {
  const stopWords = new Set([
    "about", "after", "also", "and", "are", "for", "from", "into", "that", "the", "their", "this", "with"
  ]);
  return new Set(
    (content.toLowerCase().match(/[a-z][a-z0-9-]{2,}/g) ?? []).filter((term) => !stopWords.has(term))
  );
}
