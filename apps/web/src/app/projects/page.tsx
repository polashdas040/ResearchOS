"use client";

import Link from "next/link";
import React from "react";
import { AppHeader } from "../../components/AppHeader";
import { HydrationSafeButton } from "../../components/HydrationSafeControls";
import {
  createProject,
  deleteProject,
  getStoredAccessToken,
  listProjects,
  updateProject,
  ProjectResponse
} from "../../lib/api-client";

export default function ProjectsPage() {
  const [projects, setProjects] = React.useState<ProjectResponse[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isCreating, setIsCreating] = React.useState(false);
  const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
  const [newProjectName, setNewProjectName] = React.useState("New research project");
  const [deletingProjectId, setDeletingProjectId] = React.useState<string | null>(null);
  const [editingProjectId, setEditingProjectId] = React.useState<string | null>(null);
  const [projectNameDraft, setProjectNameDraft] = React.useState("");
  const hasLocalMutations = React.useRef(false);

  React.useEffect(() => {
    let ignore = false;
    if (!getStoredAccessToken()) {
      setError("Please sign in or create an account first.");
      setIsLoading(false);
      return () => {
        ignore = true;
      };
    }
    listProjects()
      .then((response) => {
        if (!ignore && !hasLocalMutations.current) {
          setProjects(response.items);
        }
      })
      .catch((error) => {
        if (!ignore) {
          setError(error instanceof Error ? error.message : "Could not load projects.");
        }
      })
      .finally(() => {
        if (!ignore) {
          setIsLoading(false);
        }
      });
    return () => {
      ignore = true;
    };
  }, []);

  async function handleCreateProject() {
    const name = newProjectName.trim();
    if (!name) return;
    setError(null);
    setIsCreating(true);
    try {
      const project = await createProject(name);
      hasLocalMutations.current = true;
      setProjects((current) => [project, ...current]);
      setCreateDialogOpen(false);
      setNewProjectName("New research project");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not create project.");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleDeleteProject(project: ProjectResponse) {
    if (!window.confirm(`Delete "${project.name}"? This removes it from your workspace.`)) return;
    setError(null);
    setDeletingProjectId(project.id);
    try {
      await deleteProject(project.id);
      hasLocalMutations.current = true;
      setProjects((current) => current.filter((item) => item.id !== project.id));
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not delete project.");
    } finally {
      setDeletingProjectId(null);
    }
  }

  async function handleSaveProject(project: ProjectResponse) {
    const name = projectNameDraft.trim();
    if (!name) return;
    setError(null);
    try {
      const updated = await updateProject(project.id, { name });
      hasLocalMutations.current = true;
      setProjects((current) => current.map((item) => item.id === updated.id ? updated : item));
      setEditingProjectId(null);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not update project.");
    }
  }

  return (
    <main className="min-h-screen bg-[#eef2f5] text-[#172026]">
      <AppHeader />
      <section className="mx-auto max-w-6xl px-4 py-8 md:px-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Projects</h1>
            <p className="mt-1 text-sm text-[#536174]">
              {isLoading
                ? `${projects.length} active research workspaces`
                : `${projects.length} research workspaces`}
            </p>
          </div>
          <HydrationSafeButton
            type="button"
            onClick={() => setCreateDialogOpen(true)}
            disabled={isCreating}
            className="rounded bg-[#176b5b] px-4 py-2.5 text-sm font-semibold text-white"
          >
            {isCreating ? "Creating..." : "New project"}
          </HydrationSafeButton>
        </div>
        {error ? <p className="mt-4 text-sm font-medium text-[#a33a2d]">{error}</p> : null}
        {!isLoading && projects.length === 0 && !error ? (
          <p className="mt-6 rounded border border-[#d7dde6] bg-white p-4 text-sm text-[#536174]">
            No projects yet. Create one to start chatting with ResearchOS.
          </p>
        ) : null}
        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {projects.map((project) => (
            <article key={project.id} className="rounded border border-[#d7dde6] bg-white p-4 hover:border-[#96b5aa]">
              <span className="block h-2 w-10 rounded bg-emerald-500" />
              {editingProjectId === project.id ? (
                <input
                  aria-label={`Project name for ${project.name}`}
                  value={projectNameDraft}
                  onChange={(event) => setProjectNameDraft(event.target.value)}
                  className="mt-4 w-full rounded border border-[#96b5aa] px-2 py-1.5 text-sm font-semibold outline-none focus:ring-2 focus:ring-[#176b5b]/15"
                />
              ) : (
                <Link href={`/project/${project.id}`} className="mt-4 block text-base font-semibold hover:text-[#176b5b]">
                  {project.name}
                </Link>
              )}
              <span className="mt-2 block text-sm text-[#536174]">
                {project.description ?? "Research workspace"}
              </span>
              <div className="mt-4 flex items-center justify-between gap-3">
                <span className="text-xs font-medium text-[#176b5b]">Active</span>
                <div className="flex items-center gap-3">
                  {editingProjectId === project.id ? (
                    <>
                      <button type="button" onClick={() => void handleSaveProject(project)} className="text-xs font-semibold text-[#176b5b] hover:underline">Save</button>
                      <button type="button" onClick={() => setEditingProjectId(null)} className="text-xs font-semibold text-[#667386] hover:underline">Cancel</button>
                    </>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setEditingProjectId(project.id);
                        setProjectNameDraft(project.name);
                      }}
                      className="text-xs font-semibold text-[#176b5b] hover:underline"
                    >
                      Edit
                    </button>
                  )}
                  <button
                    type="button"
                    disabled={deletingProjectId === project.id}
                    onClick={() => void handleDeleteProject(project)}
                    className="text-xs font-semibold text-[#a33a2d] hover:underline disabled:cursor-wait disabled:opacity-60"
                  >
                    {deletingProjectId === project.id ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
        {createDialogOpen ? (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 p-4">
            <section role="dialog" aria-modal="true" aria-label="Create project" className="w-full max-w-md rounded-lg border border-[#cfd7df] bg-white p-5 shadow-xl">
              <h2 className="text-lg font-semibold">Create project</h2>
              <label className="mt-4 block text-sm font-medium">
                Project name
                <input
                  autoFocus
                  aria-label="New project name"
                  value={newProjectName}
                  onChange={(event) => setNewProjectName(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && newProjectName.trim() && !isCreating) void handleCreateProject();
                  }}
                  className="mt-1.5 h-10 w-full rounded border border-[#cfd7df] px-3 outline-none focus:border-[#176b5b]"
                />
              </label>
              <div className="mt-6 flex justify-end gap-2">
                <button type="button" disabled={isCreating} onClick={() => setCreateDialogOpen(false)} className="rounded border border-[#c5cfda] px-3 py-2 text-sm disabled:opacity-50">Cancel</button>
                <button type="button" disabled={isCreating || !newProjectName.trim()} onClick={() => void handleCreateProject()} className="rounded bg-[#176b5b] px-3 py-2 text-sm font-semibold text-white disabled:opacity-50">
                  {isCreating ? "Creating..." : "Create project"}
                </button>
              </div>
            </section>
          </div>
        ) : null}
      </section>
    </main>
  );
}
