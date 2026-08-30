import Link from "next/link";
import React from "react";
import { projects } from "./workspace-data";

export function ProjectSidebar() {
  return (
    <nav
      aria-label="Projects"
      className="border-b border-[#d7dde6] bg-[#f7f9fb] p-4 lg:border-b-0 lg:border-r"
    >
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold">Projects</h2>
        <Link
          href="/projects"
          className="flex h-8 w-8 items-center justify-center rounded border border-[#c5cfda] text-base font-semibold"
          aria-label="View projects"
        >
          +
        </Link>
      </div>
      <div className="space-y-2">
        {projects.map((project) => (
          <Link
            key={project.id}
            href={`/project/${project.id}`}
            className="flex w-full items-start gap-3 rounded border border-transparent px-3 py-3 text-left hover:border-[#c5cfda] hover:bg-white"
          >
            <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${project.accentClass}`} />
            <span className="min-w-0">
              <span className="block truncate text-sm font-medium">{project.name}</span>
              <span className="block truncate text-xs text-[#667386]">{project.status}</span>
            </span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
