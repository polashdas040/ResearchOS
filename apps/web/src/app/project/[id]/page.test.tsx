import { render, screen } from "@testing-library/react";
import React from "react";
import ProjectPage from "./page";

it("renders the full research workspace interface", async () => {
  render(await ProjectPage({ params: Promise.resolve({ id: "project-1" }) }));

  expect(screen.getByRole("navigation", { name: "Projects" })).toBeInTheDocument();
  expect(screen.getByRole("main", { name: "Research chat" })).toBeInTheDocument();
  expect(screen.getAllByText("Untitled").length).toBeGreaterThan(0);
  expect(screen.getByText("Add more context for higher quality generations")).toBeInTheDocument();
  expect(screen.queryByRole("toolbar", { name: "Editor toolbar" })).not.toBeInTheDocument();
  expect(screen.getAllByRole("button", { name: "AI Chat" }).length).toBeGreaterThan(0);
  expect(screen.getByRole("button", { name: /Choose from Library/ })).toBeInTheDocument();
  expect(screen.getByLabelText("Document prompt")).toBeInTheDocument();
  expect(screen.getByText("Import a research source")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Start research document" })).toBeInTheDocument();
});

it("renders an empty workspace without exposing hidden reasoning", async () => {
  render(await ProjectPage({ params: Promise.resolve({ id: "project-1" }) }));

  expect(screen.getByLabelText("Document prompt")).toBeInTheDocument();
  expect(screen.queryByText("Evidence Map")).not.toBeInTheDocument();
  expect(screen.queryByText("Evaluating feasibility")).not.toBeInTheDocument();
  expect(screen.queryByText(/chain-of-thought/i)).not.toBeInTheDocument();
});
