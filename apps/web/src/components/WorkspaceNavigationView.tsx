import React from "react";
import { FileAttachment } from "./FileAttachment";
import { ResearchRunPanel } from "./ResearchRunPanel";
import { FileReference, FileResponse } from "../lib/api-client";
import { ResearchRunState } from "./workspace-data";

export type WorkspaceContentView = "library" | "workflows" | "papers";

type WorkspaceNavigationViewProps = {
  view: WorkspaceContentView;
  projectName: string;
  files: FileResponse[];
  references: FileReference[];
  run: ResearchRunState;
  isUploadingFile: boolean;
  onFileSelected: (file: File) => Promise<void>;
  onOpenFile: (fileId: string) => Promise<void>;
  onDeleteFile: (fileId: string) => Promise<void>;
  onSearchLiterature: (query: string) => Promise<FileReference[]>;
  onSaveLiterature: (reference: FileReference) => Promise<FileResponse>;
  onBack: () => void;
};

export function WorkspaceNavigationView({
  view,
  projectName,
  files,
  references,
  run,
  isUploadingFile,
  onFileSelected,
  onOpenFile,
  onDeleteFile,
  onSearchLiterature,
  onSaveLiterature,
  onBack
}: WorkspaceNavigationViewProps) {
  const titles: Record<WorkspaceContentView, string> = {
    library: "Library",
    workflows: "Workflows",
    papers: "Find papers"
  };

  return (
    <main aria-label={`${titles[view]} workspace`} className="flex h-full min-h-0 flex-col bg-white">
      <header className="flex min-h-16 shrink-0 items-center justify-between border-b border-[#e1e6eb] px-6">
        <div className="min-w-0">
          <h1 className="text-lg font-semibold">{titles[view]}</h1>
          <p className="truncate text-xs text-[#667386]">{projectName}</p>
        </div>
        <button type="button" onClick={onBack} className="rounded border border-[#c5cfda] px-3 py-2 text-sm font-medium hover:bg-[#f5f7f8]">
          Back to editor
        </button>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
        {view === "library" ? <LibraryView files={files} references={references} isUploadingFile={isUploadingFile} onFileSelected={onFileSelected} onOpenFile={onOpenFile} onDeleteFile={onDeleteFile} /> : null}
        {view === "workflows" ? <ResearchRunPanel run={run} /> : null}
        {view === "papers" ? <PaperSearch onSearchLiterature={onSearchLiterature} onSaveLiterature={onSaveLiterature} /> : null}
      </div>
    </main>
  );
}

function LibraryView({
  files,
  references,
  isUploadingFile,
  onFileSelected,
  onOpenFile,
  onDeleteFile
}: Pick<WorkspaceNavigationViewProps, "files" | "references" | "isUploadingFile" | "onFileSelected" | "onOpenFile" | "onDeleteFile">) {
  const referencesByFile = new Map(references.map((reference) => [reference.file_id, reference]));
  return (
    <section className="mx-auto max-w-4xl">
      <FileAttachment variant="source" disabled={isUploadingFile} onFileSelected={onFileSelected} />
      <div className="mt-6 divide-y divide-[#e1e6eb] border-y border-[#e1e6eb]">
        {files.length > 0 ? files.map((file) => (
          <div key={file.id} className="flex items-center justify-between gap-4 py-4">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{file.filename}</p>
              <p className="mt-1 text-xs text-[#667386]">{file.content_type ?? "Research source"} · {file.status}</p>
              {referencesByFile.get(file.id)?.citation ? <p className="mt-2 text-sm leading-6 text-[#536174]">{referencesByFile.get(file.id)?.citation}</p> : null}
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <button type="button" onClick={() => void onOpenFile(file.id)} className="rounded border border-[#c5cfda] px-3 py-2 text-sm font-medium hover:bg-[#f5f7f8]">Open</button>
              <button
                type="button"
                onClick={() => {
                  if (window.confirm(`Delete "${file.filename}" from Library?`)) void onDeleteFile(file.id);
                }}
                className="rounded px-3 py-2 text-sm font-medium text-[#a33a2d] hover:bg-[#fff2f0]"
              >
                Delete
              </button>
            </div>
          </div>
        )) : <p className="py-8 text-sm text-[#667386]">Import a file or save a paper to build your Library.</p>}
      </div>
    </section>
  );
}

function PaperSearch({ onSearchLiterature, onSaveLiterature }: Pick<WorkspaceNavigationViewProps, "onSearchLiterature" | "onSaveLiterature">) {
  const [query, setQuery] = React.useState("");
  const [results, setResults] = React.useState<FileReference[]>([]);
  const [isSearching, setIsSearching] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [savedSourceIds, setSavedSourceIds] = React.useState<string[]>([]);
  const [savingSourceId, setSavingSourceId] = React.useState<string | null>(null);

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setError(null);
    setIsSearching(true);
    try {
      setResults(await onSearchLiterature(query.trim()));
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : "Could not search scholarly sources.");
    } finally {
      setIsSearching(false);
    }
  }

  async function handleSave(reference: FileReference) {
    setError(null);
    setSavingSourceId(reference.file_id);
    try {
      await onSaveLiterature(reference);
      setSavedSourceIds((current) => [...new Set([...current, reference.file_id])]);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save the paper to Library.");
    } finally {
      setSavingSourceId(null);
    }
  }

  return (
    <section className="mx-auto max-w-4xl">
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label="Paper search query"
          placeholder="Search by topic, method, author, or title"
          className="min-w-0 flex-1 rounded border border-[#c5cfda] px-3 py-2.5 text-sm outline-none focus:border-[#176b5b]"
        />
        <button disabled={isSearching || !query.trim()} className="rounded bg-[#176b5b] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
          {isSearching ? "Searching..." : "Search"}
        </button>
      </form>
      {error ? <p role="alert" className="mt-4 text-sm text-[#a33a2d]">{error}</p> : null}
      <div className="mt-6 divide-y divide-[#e1e6eb] border-y border-[#e1e6eb]">
        {results.map((reference) => (
          <article key={reference.file_id} className="py-4">
            <h2 className="text-sm font-semibold">{reference.filename}</h2>
            <p className="mt-1 text-sm leading-6 text-[#536174]">{reference.citation}</p>
            {reference.evidence ? <p className="mt-2 text-sm leading-6 text-[#667386]">{reference.evidence}</p> : null}
            <div className="mt-3 flex flex-wrap items-center gap-3">
              {reference.url ? <a href={reference.url} target="_blank" rel="noreferrer" className="text-sm font-medium text-[#176b5b] hover:underline">Open paper</a> : null}
              <button
                type="button"
                disabled={savingSourceId === reference.file_id || savedSourceIds.includes(reference.file_id)}
                onClick={() => void handleSave(reference)}
                className="rounded border border-[#c5cfda] px-3 py-1.5 text-sm font-medium text-[#176b5b] hover:bg-[#f5f7f8] disabled:opacity-60"
              >
                {savedSourceIds.includes(reference.file_id)
                  ? "Saved to Library"
                  : savingSourceId === reference.file_id
                    ? "Saving..."
                    : reference.pdf_url ? "Save PDF to Library" : "Save summary to Library"}
              </button>
            </div>
          </article>
        ))}
        {!isSearching && results.length === 0 ? <p className="py-8 text-sm text-[#667386]">Search scholarly indexes for verified research sources.</p> : null}
      </div>
    </section>
  );
}
