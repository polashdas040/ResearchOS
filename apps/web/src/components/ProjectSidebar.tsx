import React from "react";
import Link from "next/link";
import { ProjectResponse } from "../lib/api-client";
import { ConversationSummary } from "./workspace-data";

const PROJECT_PAGE_SIZE = 5;

type ProjectSidebarProps = {
  projects: ProjectResponse[];
  conversationsByProject: Record<string, ConversationSummary[]>;
  activeProjectId: string;
  activeConversationId: string | null;
  expandedProjectIds: string[];
  onToggleProject: (projectId: string) => void;
  onSelectConversation: (conversationId: string) => Promise<void>;
  onNewConversation: (projectId: string) => Promise<void>;
  onRenameConversation: (conversationId: string, currentTitle: string) => Promise<void>;
  onDeleteConversation: (conversationId: string) => Promise<void>;
  navigationHidden: boolean;
  onToggleNavigation: () => void;
  profileOpen: boolean;
  onToggleProfile: () => void;
  activeView: ProjectSidebarView;
  onNavigate: (view: ProjectSidebarView) => void;
};

export type ProjectSidebarView = "editor" | "library" | "workflows" | "papers" | "chat";

const workspaceNavigation: Array<{ id: Exclude<ProjectSidebarView, "editor">; label: string; beta?: boolean }> = [
  { id: "library", label: "Library" },
  { id: "workflows", label: "Workflows", beta: true },
  { id: "papers", label: "Find papers" },
  { id: "chat", label: "AI Chat" }
];

export function ProjectSidebar({
  projects,
  conversationsByProject,
  activeProjectId,
  activeConversationId,
  expandedProjectIds,
  onToggleProject,
  onSelectConversation,
  onNewConversation,
  onRenameConversation,
  onDeleteConversation,
  navigationHidden,
  onToggleNavigation,
  profileOpen,
  onToggleProfile,
  activeView,
  onNavigate
}: ProjectSidebarProps) {
  const [openConversationMenu, setOpenConversationMenu] = React.useState<string | null>(null);
  const [visibleProjectCount, setVisibleProjectCount] = React.useState(PROJECT_PAGE_SIZE);
  const orderedProjects = React.useMemo(() => {
    const activeProject = projects.find((project) => project.id === activeProjectId);
    if (!activeProject) return projects;
    return [activeProject, ...projects.filter((project) => project.id !== activeProjectId)];
  }, [activeProjectId, projects]);
  const visibleProjects = orderedProjects.slice(0, visibleProjectCount);
  const hiddenProjectCount = Math.max(orderedProjects.length - visibleProjectCount, 0);

  React.useEffect(() => {
    setVisibleProjectCount(PROJECT_PAGE_SIZE);
  }, [activeProjectId]);

  return (
    <nav
      aria-label="Projects"
      className="relative flex h-full min-h-0 flex-col overflow-hidden border-b border-[#d7dde6] bg-[#f7f9fb] lg:border-b-0 lg:border-r"
    >
      <div className="shrink-0 border-b border-[#e1e6eb] p-4">
        <div className="flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={onToggleProfile}
            className="flex min-w-0 items-center gap-2 rounded text-left"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#176b5b] text-xs font-semibold text-white">
              RO
            </span>
            <span className="truncate text-sm font-semibold">ResearchOS</span>
          </button>
          <button
            type="button"
            onClick={onToggleNavigation}
            aria-label={navigationHidden ? "Show navigation" : "Hide navigation"}
            title={navigationHidden ? "Show navigation" : "Hide navigation"}
            className="flex h-8 w-8 items-center justify-center rounded text-lg text-[#536174] hover:bg-white"
          >
            <span
              aria-hidden="true"
              className={`h-2.5 w-2.5 border-b-2 border-r-2 border-current transition-transform ${navigationHidden ? "rotate-[135deg]" : "-rotate-45"}`}
            />
          </button>
        </div>
        <div className="mt-4 space-y-1 text-sm">
          <Link href="/projects" className="flex items-center gap-2 rounded px-2 py-2 font-semibold text-[#176b5b] hover:bg-white">
            <span className="text-lg">+</span>
            <span>New</span>
          </Link>
          {workspaceNavigation.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              aria-current={activeView === item.id ? "page" : undefined}
              className={`flex w-full items-center justify-between rounded px-2 py-2 text-left hover:bg-white ${
                activeView === item.id ? "bg-white font-semibold text-[#176b5b]" : "text-[#25313d]"
              }`}
            >
              <span>{item.label}</span>
              {item.beta ? <span className="rounded bg-[#eef2f5] px-1.5 py-0.5 text-[10px] text-[#667386]">BETA</span> : null}
            </button>
          ))}
        </div>
      </div>
      <div className="flex min-h-0 flex-1 flex-col p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold">Projects</h2>
          <Link href="/projects" className="text-xs font-semibold text-[#176b5b]">Manage</Link>
        </div>
      <div aria-label="Project list" className="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
        {visibleProjects.map((project) => (
          <div key={project.id} className="rounded border border-transparent bg-white/60">
            <div className="flex items-center gap-2 px-2 py-2">
              <button
                type="button"
                onClick={() => onToggleProject(project.id)}
                aria-label={`${expandedProjectIds.includes(project.id) ? "Collapse" : "Expand"} ${project.name}`}
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#667386] hover:bg-[#eef2f5]"
              >
                <span
                  aria-hidden="true"
                  className={`h-2 w-2 border-b border-r border-current transition-transform ${expandedProjectIds.includes(project.id) ? "rotate-[-135deg]" : "rotate-45"}`}
                />
              </button>
              <Link
                href={`/project/${project.id}`}
                className={`min-w-0 flex-1 truncate text-sm font-semibold ${
                  activeProjectId === project.id ? "text-[#176b5b]" : "text-[#172026]"
                }`}
              >
                {project.name}
              </Link>
              <button
                type="button"
                onClick={() => void onNewConversation(project.id)}
                aria-label={`New conversation in ${project.name}`}
                className="text-lg leading-none text-[#176b5b]"
              >
                +
              </button>
            </div>
            {expandedProjectIds.includes(project.id) ? (
              <div className="border-t border-[#e1e6eb] px-2 py-2">
                {(conversationsByProject[project.id] ?? []).length > 0 ? (
                  <div className="space-y-1">
                    {(conversationsByProject[project.id] ?? []).map((conversation) => (
                      <div key={conversation.id} className="group relative flex items-center gap-1">
                      <button
                        key={conversation.id}
                        type="button"
                        onClick={() => void onSelectConversation(conversation.id)}
                        className={`min-w-0 flex-1 rounded px-3 py-2 text-left text-xs ${
                          activeConversationId === conversation.id
                            ? "bg-[#e3f1eb] font-semibold text-[#176b5b]"
                            : "text-[#536174] hover:bg-[#f1f4f6]"
                        }`}
                      >
                        <span className="block truncate">{conversation.title}</span>
                        <span className="mt-0.5 block text-[11px] text-[#84909d]">
                          {conversation.updatedAt}
                        </span>
                      </button>
                      <button
                        type="button"
                        aria-label={`Conversation actions for ${conversation.title}`}
                        title="Conversation actions"
                        onClick={(event) => {
                          event.stopPropagation();
                          setOpenConversationMenu((current) => current === conversation.id ? null : conversation.id);
                        }}
                        className="rounded px-1 text-lg leading-none text-[#84909d] opacity-0 hover:bg-[#e8edf0] group-hover:opacity-100"
                      >
                        ...
                      </button>
                      {openConversationMenu === conversation.id ? (
                        <div className="absolute right-2 top-8 z-10 w-28 rounded border border-[#cbd5df] bg-white p-1 text-xs shadow-lg">
                          <button
                            type="button"
                            className="block w-full rounded px-2 py-1.5 text-left hover:bg-[#f1f4f6]"
                            onClick={() => {
                              setOpenConversationMenu(null);
                              void onRenameConversation(conversation.id, conversation.title);
                            }}
                          >
                            Rename
                          </button>
                          <button
                            type="button"
                            className="block w-full rounded px-2 py-1.5 text-left text-red-700 hover:bg-[#fff2f0]"
                            onClick={() => {
                              setOpenConversationMenu(null);
                              if (window.confirm("Delete this conversation?")) {
                                void onDeleteConversation(conversation.id);
                              }
                            }}
                          >
                            Delete
                          </button>
                        </div>
                      ) : null}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="px-3 py-2 text-xs text-[#84909d]">No conversations yet</p>
                )}
              </div>
            ) : null}
          </div>
        ))}
      </div>
      {orderedProjects.length > PROJECT_PAGE_SIZE ? (
        <button
          type="button"
          onClick={() => setVisibleProjectCount((current) => (
            hiddenProjectCount > 0
              ? Math.min(current + PROJECT_PAGE_SIZE, orderedProjects.length)
              : PROJECT_PAGE_SIZE
          ))}
          className="mt-3 w-full shrink-0 rounded border border-[#d7dde6] bg-white px-3 py-2 text-xs font-semibold text-[#176b5b] hover:bg-[#eef5f2]"
        >
          {hiddenProjectCount > 0 ? `More projects (${hiddenProjectCount})` : "Show fewer"}
        </button>
      ) : null}
      </div>
      <div aria-label="Sidebar footer" className="shrink-0 border-t border-[#d7dde6] bg-[#f7f9fb] p-3">
        <details className="group">
          <summary className="flex cursor-pointer list-none items-center justify-between rounded px-2 py-2 text-sm font-medium hover:bg-white">
            <span>Setup &amp; help</span>
            <span className="text-xs text-[#667386] group-open:hidden">2/5</span>
            <span aria-hidden="true" className="hidden text-[#667386] group-open:inline">−</span>
          </summary>
          <div className="px-2 pb-2">
            <div className="mb-3 h-2 rounded-full bg-[#e1e6eb]">
              <div className="h-2 w-2/5 rounded-full bg-[#17b26a]" />
            </div>
            <div className="space-y-1 text-sm">
              {["Web Extension", "Tutorials", "Help", "Shortcuts"].map((item) => (
                <button key={item} type="button" className="block w-full rounded px-2 py-1.5 text-left hover:bg-white">
                  {item}
                </button>
              ))}
            </div>
          </div>
        </details>
        <Link href="/billing" className="mt-4 block rounded bg-[#176b5b] px-3 py-2 text-center text-sm font-semibold text-white">
          See Pricing
        </Link>
        {profileOpen ? (
          <div className="absolute bottom-16 left-4 right-4 rounded border border-[#cbd5df] bg-white p-3 text-xs shadow-lg">
            <p className="font-semibold text-[#172026]">ResearchOS account</p>
            <p className="mt-1 text-[#667386]">Manage your profile and workspace settings.</p>
            <Link href="/settings" className="mt-3 block font-semibold text-[#176b5b]">Account settings</Link>
            <Link href="/billing" className="mt-2 block font-semibold text-[#176b5b]">Billing</Link>
          </div>
        ) : null}
      </div>
    </nav>
  );
}
