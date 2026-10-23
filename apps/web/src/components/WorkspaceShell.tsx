"use client";

import React from "react";
import { ChatThread } from "./ChatThread";
import { MessageComposer } from "./MessageComposer";
import { ProjectSidebar, ProjectSidebarView } from "./ProjectSidebar";
import { StreamingMessage } from "./StreamingMessage";
import { WorkspaceContentView, WorkspaceNavigationView } from "./WorkspaceNavigationView";
import {
  AttachedFile,
  FileReference,
  FileResponse,
  createConversation,
  getConversation,
  getStoredAccessToken,
  listProjectFiles,
  listProjectFileReferences,
  deleteProjectFile,
  saveLiteratureReference,
  searchLiteratureReferences,
  listProjects,
  listConversations,
  renameConversation,
  deleteConversation,
  openProjectFile,
  streamChatMessage,
  uploadProjectFile
} from "../lib/api-client";
import {
  ChatMessage,
  ConversationSummary,
  messages as initialMessages,
  researchRun,
  ResearchRunState
} from "./workspace-data";
import {
  CitationStyle,
  citationMarker,
  citationStyles,
  formatReference
} from "../lib/citation-style";

type WorkspaceShellProps = {
  projectId: string;
};

export function WorkspaceShell({ projectId }: WorkspaceShellProps) {
  const [conversationId, setConversationId] = React.useState<string | null>(null);
  const [projects, setProjects] = React.useState<Array<{ id: string; name: string; description: string | null }>>([]);
  const [conversations, setConversations] = React.useState<ConversationSummary[]>([]);
  const [conversationsByProject, setConversationsByProject] = React.useState<Record<string, ConversationSummary[]>>({});
  const [expandedProjectIds, setExpandedProjectIds] = React.useState<string[]>([projectId]);
  const [navigationHidden, setNavigationHidden] = React.useState(false);
  const [profileOpen, setProfileOpen] = React.useState(false);
  const [messages, setMessages] = React.useState<ChatMessage[]>(initialMessages);
  const [isStreamingReply, setIsStreamingReply] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [isUploadingFile, setIsUploadingFile] = React.useState(false);
  const [attachedFiles, setAttachedFiles] = React.useState<AttachedFile[]>([]);
  const [activeContextFiles, setActiveContextFiles] = React.useState<AttachedFile[]>([]);
  const [projectFiles, setProjectFiles] = React.useState<FileResponse[]>([]);
  const [sourceReferences, setSourceReferences] = React.useState<FileReference[]>([]);
  const [sourceReferencesLoaded, setSourceReferencesLoaded] = React.useState(false);
  const [documentPrompt, setDocumentPrompt] = React.useState<string | null>(null);
  const [isAnalyzingDocument, setIsAnalyzingDocument] = React.useState(false);
  const [aiChatOpen, setAiChatOpen] = React.useState(false);
  const [workspaceView, setWorkspaceView] = React.useState<"editor" | WorkspaceContentView>("editor");
  const [citationStyle, setCitationStyle] = React.useState<CitationStyle>("IEEE");
  const [visibleChatMessageCount, setVisibleChatMessageCount] = React.useState(6);
  const chatScrollRef = React.useRef<HTMLDivElement>(null);

  const documentContextFiles = attachedFiles.length > 0 ? attachedFiles : activeContextFiles;
  const documentReferences = React.useMemo(
    () => documentContextFiles.flatMap((file, index) => {
      const reference = sourceReferences.find((item) => item.file_id === file.id);
      if (!reference) return [];
      const number = index + 1;
      return [{
        ...reference,
        number,
        citation: reference.citation.replace(/^\[\d+\]/, `[${number}]`)
      }];
    }),
    [documentContextFiles, sourceReferences]
  );
  const chatMessages = visibleChatMessages(messages);
  const visibleMessages = chatMessages.slice(-visibleChatMessageCount);
  const previousMessageCount = Math.max(0, chatMessages.length - visibleMessages.length);
  const visibleRun = buildVisibleResearchRun(messages, isStreamingReply, documentPrompt);
  const currentAgent =
    visibleRun.steps.find((step) => step.status === "running") ??
    [...visibleRun.steps].reverse().find((step) => step.status === "complete");

  React.useEffect(() => {
    setVisibleChatMessageCount(6);
  }, [conversationId]);

  React.useEffect(() => {
    const chatScroller = chatScrollRef.current;
    if (aiChatOpen && chatScroller) {
      chatScroller.scrollTop = chatScroller.scrollHeight;
    }
  }, [aiChatOpen, messages, isStreamingReply]);

  React.useEffect(() => {
    const storedPrompt = window.localStorage.getItem(`researchos.projectPrompt.${projectId}`);
    if (storedPrompt) setDocumentPrompt(storedPrompt);
    const storedCitationStyle = window.localStorage.getItem(`researchos.citationStyle.${projectId}`);
    if (citationStyles.includes(storedCitationStyle as CitationStyle)) {
      setCitationStyle(storedCitationStyle as CitationStyle);
    }
  }, [projectId]);

  function handleCitationStyleChange(style: CitationStyle) {
    setCitationStyle(style);
    window.localStorage.setItem(`researchos.citationStyle.${projectId}`, style);
  }

  React.useEffect(() => {
    let ignore = false;
    setSourceReferencesLoaded(false);
    async function loadConversation() {
      if (!getStoredAccessToken()) {
        return;
      }
      try {
        const projectList = await listProjects();
        const [projectFiles, projectReferences] = await Promise.all([
          listProjectFiles(projectId),
          listProjectFileReferences(projectId)
        ]);
        const conversationLists = await Promise.all(
          projectList.items.map(async (project) => [project.id, await listConversations(project.id)] as const)
        );
        setProjects(projectList.items);
        setConversationsByProject(
          Object.fromEntries(
            conversationLists.map(([id, response]) => [
              id,
              response.items.map((item, index) => ({
                id: item.id,
                title: item.title,
                updatedAt: index === 0 ? "Active" : "Saved"
              }))
            ])
          )
        );
        const currentConversations = await listConversations(projectId);
        const conversation =
          currentConversations.items[0] ??
          (await createConversation(projectId, "Research workspace conversation"));
        if (!ignore) {
          const summaries = currentConversations.items.map((item, index) => ({
              id: item.id,
              title: item.title,
              updatedAt: index === 0 ? "Active" : "Saved"
            }));
          setConversations(summaries);
          setConversationsByProject((current) => ({ ...current, [projectId]: summaries }));
        }
        const conversationWithMessages = await getConversation(conversation.id);
        if (!ignore) {
          setActiveContextFiles(
            projectFiles.items
              .filter((file) => file.status === "READY")
              .slice(0, 10)
              .map((file) => ({ ...file, downloadUrl: "" }))
          );
          setProjectFiles(projectFiles.items);
          setSourceReferences(projectReferences.items);
          setSourceReferencesLoaded(true);
          setConversationId(conversation.id);
          const loadedMessages = (conversationWithMessages.messages?.items ?? []).map((message) => ({
              id: message.id,
              author: message.message_type === "USER" ? "Researcher" : "ResearchOS",
              content: message.content,
              tone: message.message_type === "USER" ? "user" : "assistant"
            }) satisfies ChatMessage);
          setMessages(loadedMessages);
          setDocumentPrompt(
            window.localStorage.getItem(`researchos.projectPrompt.${projectId}`) ??
            loadedMessages.find((message) => message.tone === "user")?.content ??
            null
          );
        }
      } catch (error) {
        if (!ignore) {
          setError(error instanceof Error ? error.message : "Could not load conversation.");
        }
      }
    }

    loadConversation();
    return () => {
      ignore = true;
    };
  }, [projectId]);

  async function handleNewConversation() {
    await handleNewConversationForProject(projectId);
  }

  async function handleNewConversationForProject(targetProjectId: string) {
    setError(null);
    try {
      const requestedTitle = window.prompt("Conversation name", "New research conversation");
      if (!requestedTitle?.trim()) return;
      const conversation = await createConversation(targetProjectId, requestedTitle.trim());
      setConversationId(conversation.id);
      setConversations((current) => [
        ...current.map((item) => ({ ...item, active: false })),
        { id: conversation.id, title: conversation.title, updatedAt: "Active", active: true }
      ]);
      setConversationsByProject((current) => ({
        ...current,
        [targetProjectId]: [
          ...(current[targetProjectId] ?? []).map((item) => ({ ...item, active: false })),
          { id: conversation.id, title: conversation.title, updatedAt: "Active", active: true }
        ]
      }));
      setExpandedProjectIds((current) => current.includes(targetProjectId) ? current : [...current, targetProjectId]);
      setMessages([]);
      setDocumentPrompt(null);
      setAiChatOpen(false);
      window.localStorage.removeItem(`researchos.projectPrompt.${targetProjectId}`);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not create conversation.");
    }
  }

  async function handleRenameConversation(conversationToRenameId: string, currentTitle: string) {
    const title = window.prompt("Conversation name", currentTitle);
    if (!title?.trim()) return;
    try {
      const updated = await renameConversation(conversationToRenameId, title.trim());
      setConversationsByProject((current) =>
        Object.fromEntries(
          Object.entries(current).map(([id, items]) => [
            id,
            items.map((item) => item.id === updated.id ? { ...item, title: updated.title } : item)
          ])
        )
      );
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not rename conversation.");
    }
  }

  async function handleDeleteConversation(conversationToDeleteId: string) {
    try {
      await deleteConversation(conversationToDeleteId);
      setConversationsByProject((current) =>
        Object.fromEntries(
          Object.entries(current).map(([id, items]) => [id, items.filter((item) => item.id !== conversationToDeleteId)])
        )
      );
      if (conversationId === conversationToDeleteId) {
        setConversationId(null);
        setMessages([]);
        setDocumentPrompt(null);
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not delete conversation.");
    }
  }

  async function handleSelectConversation(selectedConversationId: string) {
    setError(null);
    try {
      const conversation = await getConversation(selectedConversationId);
      setConversationId(conversation.id);
      const loadedMessages = (conversation.messages?.items ?? []).map((message) => ({
          id: message.id,
          author: message.message_type === "USER" ? "Researcher" : "ResearchOS",
          content: message.content,
          tone: message.message_type === "USER" ? "user" : "assistant"
        }) satisfies ChatMessage);
      setMessages(loadedMessages);
      setDocumentPrompt(
        window.localStorage.getItem(`researchos.projectPrompt.${projectId}`) ??
        loadedMessages.find((message) => message.tone === "user")?.content ??
        null
      );
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not load conversation.");
    }
  }

  async function handleSendMessage(
    content: string,
    hidden = false,
    historyOverride?: ChatMessage[]
  ): Promise<string> {
    let assistantContent = "";
    setError(null);
    try {
      const attachmentSummary = attachedFiles.map((file) => file.filename).join(", ");
      const filesForRequest = attachedFiles.length > 0 ? attachedFiles : activeContextFiles;
      const attachmentIds = filesForRequest.map((file) => file.id);
      const messageContent = content || (attachmentSummary ? `Attached file: ${attachmentSummary}` : "");
      const activeConversationId =
        conversationId ??
        (await createConversation(projectId, "Research workspace conversation")).id;
      setConversationId(activeConversationId);
      const userMessageId = crypto.randomUUID();
      const assistantMessageId = crypto.randomUUID();
      setMessages((current) => [
        ...current,
        {
          id: userMessageId,
          author: "Researcher",
          content: messageContent,
          tone: "user",
          hidden,
          attachments: attachedFiles.map((file) => ({
            id: file.id,
            filename: file.filename,
            contentType: file.content_type ?? "application/pdf"
          }))
        },
        {
          id: assistantMessageId,
          author: "ResearchOS",
          content: "",
          tone: "assistant",
          hidden
        }
      ]);
      setIsStreamingReply(true);
      const historyMessages = (historyOverride ?? visibleChatMessages(messages))
        .filter((message) => message.content.trim())
        .slice(-40)
        .map((message) => ({
          role: message.tone === "user" ? "user" as const : "assistant" as const,
          content: message.content
        }));
      let referenceContext = "";
      if (!hidden && messageContent) {
        const attachedReferences = attachmentIds.flatMap((fileId, index) => {
          const reference = sourceReferences.find((item) => item.file_id === fileId);
          return reference ? [{ ...reference, number: index + 1 }] : [];
        });
        if (attachedReferences.length > 0) {
          referenceContext = buildReferenceContext(attachedReferences, citationStyle);
        } else if (attachmentIds.length === 0) {
          try {
            referenceContext = buildReferenceContext(
              await handleLiteratureSearch(messageContent),
              citationStyle
            );
          } catch {
            referenceContext = "";
          }
        }
      }
      await streamChatMessage(
        activeConversationId,
        messageContent,
        (delta) => {
          assistantContent += delta;
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantMessageId
                ? { ...message, content: `${message.content}${delta}` }
                : message
            )
          );
        },
        attachmentIds,
        {
          history: historyMessages,
          citationStyle,
          referenceContext,
          requireReferences: !hidden
        }
      );
      if (attachedFiles.length > 0) {
        setActiveContextFiles(attachedFiles);
      }
      setAttachedFiles([]);
      return assistantContent;
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not send message.");
      return "";
    } finally {
      setIsStreamingReply(false);
    }
  }

  async function handleResubmitMessage(messageId: string, content: string) {
    const messageIndex = messages.findIndex((message) => message.id === messageId);
    if (messageIndex < 0) return;
    const history = messages.slice(0, messageIndex).filter((message) => !message.hidden);
    setMessages(history);
    await handleSendMessage(content, false, history);
  }

  async function handleStartDocument(content: string) {
    const prompt = content || attachedFiles.map((file) => file.filename).join(", ");
    setDocumentPrompt(prompt);
    window.localStorage.setItem(`researchos.projectPrompt.${projectId}`, prompt);
    if (attachedFiles.length > 0) {
      setActiveContextFiles(attachedFiles);
      setAttachedFiles([]);
    }
    setIsAnalyzingDocument(true);
    await new Promise((resolve) => window.setTimeout(resolve, 700));
    setIsAnalyzingDocument(false);
  }

  async function handleSectionGeneration(content: string): Promise<string> {
    return handleSendMessage(content, true);
  }

  async function handleLiteratureSearch(query: string): Promise<FileReference[]> {
    const response = await searchLiteratureReferences(projectId, query, 5);
    return response.items.map((reference) => ({
      number: reference.number,
      file_id: `literature:${reference.source_id}`,
      filename: reference.title,
      citation: reference.citation,
      evidence: reference.evidence,
      url: reference.url ?? undefined,
      source_type: "literature" as const,
      source_id: reference.source_id,
      pdf_url: reference.pdf_url ?? undefined
    }));
  }

  async function handleSaveLiterature(reference: FileReference): Promise<FileResponse> {
    const saved = await saveLiteratureReference(projectId, {
      number: reference.number,
      source_id: reference.source_id ?? reference.file_id.replace(/^literature:/, ""),
      title: reference.filename,
      citation: reference.citation,
      evidence: reference.evidence ?? "",
      url: reference.url,
      pdf_url: reference.pdf_url
    });
    setProjectFiles((current) => [saved, ...current.filter((file) => file.id !== saved.id)]);
    const refreshed = await listProjectFileReferences(projectId);
    setSourceReferences(refreshed.items);
    setSourceReferencesLoaded(true);
    return saved;
  }

  async function handleDeleteFile(fileId: string) {
    setError(null);
    try {
      await deleteProjectFile(fileId);
      setProjectFiles((current) => current.filter((file) => file.id !== fileId));
      setSourceReferences((current) => current.filter((reference) => reference.file_id !== fileId));
      setAttachedFiles((current) => current.filter((file) => file.id !== fileId));
      setActiveContextFiles((current) => current.filter((file) => file.id !== fileId));
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Could not delete the Library file.");
    }
  }

  function handleAttachLibraryFile(file: FileResponse) {
    setAttachedFiles((current) => current.some((item) => item.id === file.id)
      ? current
      : [...current, { ...file, downloadUrl: "" }]);
  }

  async function handleRefreshLibrary(): Promise<FileResponse[]> {
    const response = await listProjectFiles(projectId);
    setProjectFiles(response.items);
    return response.items;
  }

  async function handleFileSelected(file: File) {
    setError(null);
    setIsUploadingFile(true);
    try {
      const uploaded = await uploadProjectFile(projectId, file);
      setProjectFiles((current) => [uploaded, ...current.filter((item) => item.id !== uploaded.id)]);
      setAttachedFiles((current) => [
        ...current,
        {
          ...uploaded,
          downloadUrl: ""
        }
      ]);
      try {
        const projectReferences = await listProjectFileReferences(projectId);
        setSourceReferences(projectReferences.items);
        setSourceReferencesLoaded(true);
      } catch {
        setError("File uploaded, but its reference metadata could not be refreshed.");
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not upload file.");
    } finally {
      setIsUploadingFile(false);
    }
  }

  function handleWorkspaceNavigation(view: ProjectSidebarView) {
    if (view === "chat") {
      setAiChatOpen(true);
      return;
    }
    setAiChatOpen(false);
    setWorkspaceView(view);
  }

  return (
    <div className="fixed inset-0 overflow-hidden bg-[#f6f7f8] text-[#202124]">
      <div className={`grid h-full min-h-0 grid-cols-1 ${navigationHidden
        ? aiChatOpen ? "lg:grid-cols-[minmax(0,1fr)_340px]" : "lg:grid-cols-[minmax(0,1fr)]"
        : aiChatOpen ? "lg:grid-cols-[260px_minmax(0,1fr)_340px]" : "lg:grid-cols-[260px_minmax(0,1fr)]"}`}>
        {navigationHidden ? (
          <button
            type="button"
            onClick={() => setNavigationHidden(false)}
            aria-label="Show navigation"
            title="Show navigation"
            className="fixed left-3 top-3 z-20 flex h-9 w-9 items-center justify-center rounded border border-[#c5cfda] bg-white text-[#536174] shadow-sm hover:bg-[#f5f7f8]"
          >
            <span
              aria-hidden="true"
              className="h-2.5 w-2.5 rotate-[135deg] border-b-2 border-r-2 border-current"
            />
          </button>
        ) : null}
        {!navigationHidden ? (
          <ProjectSidebar
            projects={projects}
            conversationsByProject={conversationsByProject}
            activeProjectId={projectId}
            activeConversationId={conversationId}
            expandedProjectIds={expandedProjectIds}
            onToggleProject={(id) => setExpandedProjectIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id])}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversationForProject}
            onRenameConversation={handleRenameConversation}
            onDeleteConversation={handleDeleteConversation}
            navigationHidden={navigationHidden}
            onToggleNavigation={() => setNavigationHidden((current) => !current)}
            profileOpen={profileOpen}
            onToggleProfile={() => setProfileOpen((current) => !current)}
            activeView={aiChatOpen ? "chat" : workspaceView}
            onNavigate={handleWorkspaceNavigation}
          />
        ) : null}
        <div className={`flex h-full min-h-0 min-w-0 flex-col ${navigationHidden ? "pl-14" : ""}`}>
          {workspaceView === "editor" ? <ChatThread
            documentPrompt={documentPrompt}
            sourceReferences={documentReferences}
            sourceReferencesLoaded={sourceReferencesLoaded}
            onStartDocument={handleStartDocument}
            onGenerateSection={handleSectionGeneration}
            onSearchLiterature={handleLiteratureSearch}
            onToggleAiChat={() => setAiChatOpen((current) => !current)}
            onFileSelected={handleFileSelected}
            libraryFiles={projectFiles}
            onAttachLibraryFile={handleAttachLibraryFile}
            onRefreshLibrary={handleRefreshLibrary}
            isUploadingFile={isUploadingFile}
            attachedFiles={attachedFiles}
            onOpenFile={openProjectFile}
            error={error}
            isGenerating={isAnalyzingDocument}
            citationStyle={citationStyle}
            onCitationStyleChange={handleCitationStyleChange}
          /> : <WorkspaceNavigationView
            view={workspaceView}
            projectName={projects.find((project) => project.id === projectId)?.name ?? "Research project"}
            files={projectFiles}
            references={sourceReferences}
            run={buildVisibleResearchRun(messages, isStreamingReply, documentPrompt)}
            isUploadingFile={isUploadingFile}
            onFileSelected={handleFileSelected}
            onOpenFile={openProjectFile}
            onDeleteFile={handleDeleteFile}
            onSearchLiterature={handleLiteratureSearch}
            onSaveLiterature={handleSaveLiterature}
            onBack={() => setWorkspaceView("editor")}
          />}
        </div>
        {aiChatOpen ? <aside aria-label="Research assistant" className="flex h-full min-h-0 flex-col border-l border-[#d7dde6] bg-white">
          <div className="flex min-h-14 items-center justify-between border-b border-[#d7dde6] px-4">
            <h2 className="font-semibold">AI Chat</h2>
            <select
              aria-label="Chat citation style"
              value={citationStyle}
              onChange={(event) => handleCitationStyleChange(event.target.value as CitationStyle)}
              className="rounded border border-[#c5cfda] bg-white px-2 py-1 text-xs text-[#394653]"
            >
              {citationStyles.map((style) => <option key={style} value={style}>{style}</option>)}
            </select>
          </div>
          {currentAgent ? (
            <div aria-label="Current agent" className="border-b border-[#d7dde6] bg-[#f4faf7] px-4 py-3">
              <div className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${isStreamingReply ? "animate-pulse bg-amber-500" : "bg-emerald-500"}`} />
                <p className="min-w-0 flex-1 truncate text-sm font-semibold text-[#172026]">{currentAgent.agent}</p>
                <span className="text-xs text-[#667386]">{isStreamingReply ? "Working" : "Ready"}</span>
              </div>
              <p className="mt-1 truncate pl-4 text-xs text-[#667386]">{currentAgent.label}</p>
            </div>
          ) : null}
          <div ref={chatScrollRef} aria-label="Chat history" className="min-h-0 flex-1 overflow-y-auto px-4 py-5">
            {chatMessages.length > 0 ? (
              <div className="space-y-5">
                {previousMessageCount > 0 ? (
                  <div className="flex justify-center">
                    <button
                      type="button"
                      onClick={() => setVisibleChatMessageCount((count) => Math.min(chatMessages.length, count + 6))}
                      className="rounded-full border border-[#c5cfda] bg-white px-4 py-2 text-xs font-semibold text-[#176b5b] hover:bg-[#f4faf7]"
                    >
                      Load previous ({previousMessageCount})
                    </button>
                  </div>
                ) : null}
                {visibleMessages.map((message) => (
                  message.content ? (
                    <StreamingMessage
                      key={message.id}
                      message={message}
                      compact
                      onResubmit={message.tone === "user" ? handleResubmitMessage : undefined}
                    />
                  ) : null
                ))}
                {isStreamingReply && visibleMessages.at(-1)?.tone === "assistant" && !visibleMessages.at(-1)?.content ? (
                  <div role="status" className="flex items-center gap-2 text-sm text-[#667386]">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-[#176b5b]" />
                    {currentAgent?.agent ?? "ResearchOS"} is working...
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="mx-auto mt-12 max-w-[260px] text-center text-sm leading-6 text-[#667386]">
                Ask about the current document, project sources, or supporting literature.
              </p>
            )}
          </div>
          {documentPrompt ? (
            <div className="border-t border-[#d7dde6] bg-[#fbfcfd] p-3">
              <MessageComposer
                onSubmit={async (content) => { await handleSendMessage(content); }}
                onFileSelected={handleFileSelected}
                onOpenFile={openProjectFile}
                isUploadingFile={isUploadingFile}
                attachedFiles={attachedFiles}
                compact
              />
            </div>
          ) : null}
        </aside> : null}
      </div>
    </div>
  );
}

function buildReferenceContext(references: FileReference[], citationStyle: CitationStyle) {
  return references.map((reference) => (
    `${formatReference(reference, citationStyle)}\n` +
    `INLINE CITATION: ${citationMarker(reference, citationStyle)}\n` +
    `EVIDENCE: ${reference.evidence ?? "See the attached source excerpts."}`
  )).join("\n\n");
}

function visibleChatMessages(messages: ChatMessage[]) {
  return messages.filter((message, index) => {
    if (message.hidden) return false;
    if (index < 2) return false;
    const previous = messages[index - 1];
    if (message.tone === "user" && /^Write the .+ section for /i.test(message.content)) return false;
    if (message.tone === "assistant" && previous?.tone === "user" && /^Write the .+ section for /i.test(previous.content)) return false;
    return true;
  });
}

function buildVisibleResearchRun(
  messages: ChatMessage[],
  isStreamingReply: boolean,
  promptOverride?: string | null
): ResearchRunState {
  const prompt = promptOverride ?? messages.find((message) => message.tone === "user")?.content;
  if (!prompt) {
    return researchRun;
  }

  return {
    ...researchRun,
    prompt,
    startedAt: "Now",
    elapsed: isStreamingReply ? "Running" : "Complete",
    steps: [
      {
        label: "Input analyzer",
        agent: "Input Analyzer",
        status: "complete",
        detail: "Prompt accepted and converted into a research objective."
      },
      {
        label: "Research decomposer",
        agent: "Research Decomposer",
        status: "complete",
        detail: "Research objective split into literature, evidence, and writing tasks."
      },
      {
        label: "Literature search",
        agent: "Literature Search Agent",
        status: isStreamingReply ? "running" : "complete",
        detail: isStreamingReply ? "Finding relevant sources." : "Initial evidence pass complete."
      },
      {
        label: "Methodology analysis",
        agent: "Methodology Analysis Agent",
        status: isStreamingReply ? "waiting" : "complete",
        detail: "Checks methods, assumptions, and reproducibility constraints."
      },
      {
        label: "Evidence verification",
        agent: "Evidence Agent",
        status: isStreamingReply ? "waiting" : "complete",
        detail: "Maps claims to evidence IDs before final writing."
      },
      {
        label: "Paper writer",
        agent: "Academic Writing Agent",
        status: isStreamingReply ? "waiting" : "running",
        detail: "Drafts section text only from available context and evidence."
      },
      {
        label: "Final reviewer",
        agent: "Final Reviewer",
        status: "waiting",
        detail: "Waiting for a complete draft."
      }
    ],
    canCancel: isStreamingReply,
    sources: isStreamingReply ? ["Searching"] : ["Conversation context"],
    toolsUsed: isStreamingReply ? ["literature.search", "document.search"] : ["model.generate"],
    cost: "tracked by usage events",
    artifacts: isStreamingReply ? [] : ["Draft workspace"]
  };
}
