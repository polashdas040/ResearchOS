import React from "react";
import { AppHeader } from "./AppHeader";
import { ArtifactPanel } from "./ArtifactPanel";
import { ChatThread } from "./ChatThread";
import { ConversationSidebar } from "./ConversationSidebar";
import { ProjectSidebar } from "./ProjectSidebar";
import { ResearchRunPanel } from "./ResearchRunPanel";

export function WorkspaceShell() {
  return (
    <div className="min-h-screen bg-[#eef2f5] text-[#172026]">
      <AppHeader />
      <div className="grid min-h-[calc(100vh-4rem)] grid-cols-1 lg:grid-cols-[240px_260px_minmax(0,1fr)_320px]">
        <ProjectSidebar />
        <ConversationSidebar />
        <div className="flex min-w-0 flex-col">
          <ChatThread />
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
