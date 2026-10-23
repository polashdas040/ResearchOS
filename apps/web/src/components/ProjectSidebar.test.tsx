import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { expect, it, vi } from "vitest";
import { ProjectSidebar } from "./ProjectSidebar";

const projects = Array.from({ length: 8 }, (_, index) => ({
  id: `project-${index + 1}`,
  name: `Project ${index + 1}`,
  description: null
}));

it("shows a scrollable project subset and reveals more projects in batches", () => {
  render(
    <ProjectSidebar
      projects={projects}
      conversationsByProject={{}}
      activeProjectId="project-8"
      activeConversationId={null}
      expandedProjectIds={[]}
      onToggleProject={vi.fn()}
      onSelectConversation={vi.fn()}
      onNewConversation={vi.fn()}
      onRenameConversation={vi.fn()}
      onDeleteConversation={vi.fn()}
      navigationHidden={false}
      onToggleNavigation={vi.fn()}
      profileOpen={false}
      onToggleProfile={vi.fn()}
      activeView="editor"
      onNavigate={vi.fn()}
    />
  );

  const projectList = screen.getByLabelText("Project list");
  expect(projectList).toHaveClass("overflow-y-auto");
  expect(projectList).toHaveClass("min-h-0", "flex-1");
  expect(screen.getByLabelText("Sidebar footer")).toHaveClass("shrink-0");
  expect(screen.getByText("Setup & help").closest("details")).not.toHaveAttribute("open");
  expect(screen.getByRole("link", { name: "Project 8" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Project 4" })).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "Project 5" })).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "More projects (3)" }));

  expect(screen.getByRole("link", { name: "Project 7" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Show fewer" })).toBeInTheDocument();
});
