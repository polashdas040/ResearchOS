"use client";

import Link from "next/link";
import React from "react";
import { AppHeader } from "../../components/AppHeader";
import { HydrationSafeButton } from "../../components/HydrationSafeControls";
import {
  createProject,
  getStoredAccessToken,
  listProjects,
  ProjectResponse
} from "../../lib/api-client";

export default function ProjectsPage() {
  const [projects, setProjects] = React.useState<ProjectResponse[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isCreating, setIsCreating] = React.useState(false);

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
        if (!ignore) {
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
    const name = window.prompt("Project name", "New research project");
    if (!name?.trim()) {
      return;
    }
    setError(null);
    setIsCreating(true);
    try {
      const project = await createProject(name.trim());
      setProjects((current) => [project, ...current]);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not create project.");
    } finally {
      setIsCreating(false);
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
            onClick={handleCreateProject}
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
            <Link
              key={project.id}
              href={`/project/${project.id}`}
              className="rounded border border-[#d7dde6] bg-white p-4 hover:border-[#96b5aa]"
            >
              <span className="block h-2 w-10 rounded bg-emerald-500" />
              <span className="mt-4 block text-base font-semibold">{project.name}</span>
              <span className="mt-2 block text-sm text-[#536174]">
                {project.description ?? "Research workspace"}
              </span>
              <span className="mt-4 inline-block text-xs font-medium text-[#176b5b]">
                Active
              </span>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
