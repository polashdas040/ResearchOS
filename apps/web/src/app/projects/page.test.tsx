import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { afterEach, vi } from "vitest";
import ProjectsPage from "./page";

afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

it("renders the projects shell", () => {
  render(<ProjectsPage />);

  expect(screen.getByRole("heading", { name: "Projects" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "New project" })).toBeInTheDocument();
  expect(screen.getByText("0 research workspaces")).toBeInTheDocument();
  expect(screen.getByText("Please sign in or create an account first.")).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /ADNI Literature Review/ })).not.toBeInTheDocument();
});

it("creates a project from the in-page dialog", async () => {
  localStorage.setItem("researchos.access_token", "access-token");
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], total: 0, limit: 50, offset: 0 }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    }))
    .mockResolvedValueOnce(new Response(JSON.stringify({
      id: "project-1",
      organization_id: "organization-1",
      created_by_user_id: "user-1",
      name: "Browser QA",
      description: null,
      created_at: "2026-10-22T00:00:00Z",
      updated_at: "2026-10-22T00:00:00Z"
    }), { status: 201, headers: { "Content-Type": "application/json" } }));
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

  render(<ProjectsPage />);
  await waitFor(() => expect(screen.getByText("No projects yet. Create one to start chatting with ResearchOS.")).toBeInTheDocument());
  fireEvent.click(screen.getByRole("button", { name: "New project" }));
  const dialog = screen.getByRole("dialog", { name: "Create project" });
  fireEvent.change(screen.getByLabelText("New project name"), { target: { value: "Browser QA" } });
  fireEvent.click(screen.getByRole("button", { name: "Create project" }));

  expect(await screen.findByRole("link", { name: "Browser QA" })).toBeInTheDocument();
  expect(dialog).not.toBeInTheDocument();
  expect(fetchMock).toHaveBeenLastCalledWith(
    "http://localhost:8000/projects",
    expect.objectContaining({ method: "POST" })
  );
});

it("keeps a newly created project when the initial list request finishes later", async () => {
  localStorage.setItem("researchos.access_token", "access-token");
  let resolveList!: (response: Response) => void;
  const pendingList = new Promise<Response>((resolve) => {
    resolveList = resolve;
  });
  const fetchMock = vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
    if (init?.method === "POST") {
      return Promise.resolve(new Response(JSON.stringify({
        id: "project-1",
        organization_id: "organization-1",
        created_by_user_id: "user-1",
        name: "Evidence-Grounded AI Agents",
        description: null,
        created_at: "2026-10-22T00:00:00Z",
        updated_at: "2026-10-22T00:00:00Z"
      }), { status: 201, headers: { "Content-Type": "application/json" } }));
    }
    return pendingList;
  });
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

  render(<ProjectsPage />);
  fireEvent.click(screen.getByRole("button", { name: "New project" }));
  fireEvent.change(screen.getByLabelText("New project name"), {
    target: { value: "Evidence-Grounded AI Agents" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Create project" }));
  expect(await screen.findByRole("link", { name: "Evidence-Grounded AI Agents" })).toBeInTheDocument();

  resolveList(new Response(JSON.stringify({ items: [], total: 0, limit: 50, offset: 0 }), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  }));

  await waitFor(() => expect(screen.getByText("1 research workspaces")).toBeInTheDocument());
  expect(screen.getByRole("link", { name: "Evidence-Grounded AI Agents" })).toBeInTheDocument();
});

it("deletes a project from the management page", async () => {
  localStorage.setItem("researchos.access_token", "access-token");
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({
      items: [{
        id: "project-1",
        organization_id: "organization-1",
        created_by_user_id: "user-1",
        name: "AI Evaluation",
        description: "Research workspace",
        created_at: "2026-10-22T00:00:00Z",
        updated_at: "2026-10-22T00:00:00Z"
      }],
      total: 1,
      limit: 50,
      offset: 0
    }), { status: 200, headers: { "Content-Type": "application/json" } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({
      id: "project-1",
      organization_id: "organization-1",
      created_by_user_id: "user-1",
      name: "AI Agent Evaluation",
      description: "Research workspace",
      created_at: "2026-10-22T00:00:00Z",
      updated_at: "2026-10-22T01:00:00Z"
    }), { status: 200, headers: { "Content-Type": "application/json" } }))
    .mockResolvedValueOnce(new Response(null, { status: 204 }));
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);
  vi.spyOn(window, "confirm").mockReturnValue(true);

  render(<ProjectsPage />);
  expect(await screen.findByRole("link", { name: "AI Evaluation" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Edit" }));
  fireEvent.change(screen.getByLabelText("Project name for AI Evaluation"), {
    target: { value: "AI Agent Evaluation" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Save" }));
  expect(await screen.findByRole("link", { name: "AI Agent Evaluation" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Delete" }));

  await waitFor(() => expect(screen.queryByRole("link", { name: "AI Agent Evaluation" })).not.toBeInTheDocument());
  expect(fetchMock).toHaveBeenLastCalledWith(
    "http://localhost:8000/projects/project-1",
    expect.objectContaining({ method: "DELETE" })
  );
});
