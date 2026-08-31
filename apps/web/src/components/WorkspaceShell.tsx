"use client";

import React from "react";
import { AppHeader } from "./AppHeader";
import { ArtifactPanel } from "./ArtifactPanel";
import { ChatThread } from "./ChatThread";
import { ConversationSidebar } from "./ConversationSidebar";
import { ProjectSidebar } from "./ProjectSidebar";
import { ResearchRunPanel } from "./ResearchRunPanel";
import {
  createConversation,
  getConversation,
  getStoredAccessToken,
  listConversations,
  streamChatMessage,
  uploadProjectFile
} from "../lib/api-client";
import { ChatMessage, messages as demoMessages } from "./workspace-data";

type WorkspaceShellProps = {
  projectId: string;
};

export function WorkspaceShell({ projectId }: WorkspaceShellProps) {
  const [conversationId, setConversationId] = React.useState<string | null>(null);
  const [messages, setMessages] = React.useState<ChatMessage[]>(demoMessages);
  const [error, setError] = React.useState<string | null>(null);
  const [isUploadingFile, setIsUploadingFile] = React.useState(false);

  React.useEffect(() => {
    let ignore = false;
    async function loadConversation() {
      if (!getStoredAccessToken()) {
        return;
      }
      try {
        const conversations = await listConversations(projectId);
        const conversation =
          conversations.items[0] ??
          (await createConversation(projectId, "Research workspace conversation"));
        const conversationWithMessages = await getConversation(conversation.id);
        if (!ignore) {
          setConversationId(conversation.id);
          setMessages(
            (conversationWithMessages.messages?.items ?? []).map((message) => ({
              id: message.id,
              author: message.message_type === "USER" ? "Researcher" : "ResearchOS",
              content: message.content,
              tone: message.message_type === "USER" ? "user" : "assistant"
            }))
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

  async function handleSendMessage(content: string) {
    setError(null);
    try {
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
          content,
          tone: "user"
        },
        {
          id: assistantMessageId,
          author: "ResearchOS",
          content: "",
          tone: "assistant"
        }
      ]);
      await streamChatMessage(activeConversationId, content, (delta) => {
        setMessages((current) =>
          current.map((message) =>
            message.id === assistantMessageId
              ? { ...message, content: `${message.content}${delta}` }
              : message
          )
        );
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not send message.");
    }
  }

  async function handleFileSelected(file: File) {
    setError(null);
    setIsUploadingFile(true);
    try {
      const uploaded = await uploadProjectFile(projectId, file);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          author: "ResearchOS",
          content: `Attached ${uploaded.filename} (${uploaded.status}).`,
          tone: "system"
        }
      ]);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not upload file.");
    } finally {
      setIsUploadingFile(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#eef2f5] text-[#172026]">
      <AppHeader />
      <div className="grid min-h-[calc(100vh-4rem)] grid-cols-1 lg:grid-cols-[240px_260px_minmax(0,1fr)_320px]">
        <ProjectSidebar />
        <ConversationSidebar />
        <div className="flex min-w-0 flex-col">
          <ChatThread
            messages={messages}
            onSendMessage={handleSendMessage}
            onFileSelected={handleFileSelected}
            isUploadingFile={isUploadingFile}
            error={error}
          />
        </div>
        <div className="grid bg-[#f7f9fb] lg:grid-rows-[auto_1fr]">
          <div className="border-t border-[#d7dde6] p-4 lg:border-l lg:border-t-0">
            <ResearchRunPanel />
          </div>
          <ArtifactPanel />
        </div>
      </div>
    </div>
  );
}
