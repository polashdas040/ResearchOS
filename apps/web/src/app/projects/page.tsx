import Link from "next/link";
import React from "react";
import { AppHeader } from "../../components/AppHeader";
import { HydrationSafeButton } from "../../components/HydrationSafeControls";
import { projects } from "../../components/workspace-data";

export default function ProjectsPage() {
  return (
    <main className="min-h-screen bg-[#eef2f5] text-[#172026]">
      <AppHeader />
      <section className="mx-auto max-w-6xl px-4 py-8 md:px-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Projects</h1>
            <p className="mt-1 text-sm text-[#536174]">3 active research workspaces</p>
          </div>
          <HydrationSafeButton
            type="button"
            className="rounded bg-[#176b5b] px-4 py-2.5 text-sm font-semibold text-white"
          >
            New project
          </HydrationSafeButton>
        </div>
        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={`/project/${project.id}`}
              className="rounded border border-[#d7dde6] bg-white p-4 hover:border-[#96b5aa]"
            >
              <span className={`block h-2 w-10 rounded ${project.accentClass}`} />
              <span className="mt-4 block text-base font-semibold">{project.name}</span>
              <span className="mt-2 block text-sm text-[#536174]">{project.focus}</span>
              <span className="mt-4 inline-block text-xs font-medium text-[#176b5b]">
                {project.status}
              </span>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
