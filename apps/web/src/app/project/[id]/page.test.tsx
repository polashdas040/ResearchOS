import { render, screen } from "@testing-library/react";
import React from "react";
import ProjectPage from "./page";

it("renders the full research workspace interface", async () => {
  render(await ProjectPage({ params: Promise.resolve({ id: "demo" }) }));

  expect(screen.getByRole("navigation", { name: "Projects" })).toBeInTheDocument();
  expect(screen.getByRole("navigation", { name: "Conversations" })).toBeInTheDocument();
  expect(screen.getByRole("main", { name: "Research chat" })).toBeInTheDocument();
  expect(screen.getByRole("complementary", { name: "Artifacts" })).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "Research run" })).toBeInTheDocument();
  expect(screen.getByText("Biomarker evidence synthesis")).toBeInTheDocument();
  expect(screen.getByText("Citation validation in progress")).toBeInTheDocument();
  expect(screen.getByPlaceholderText("Ask ResearchOS...")).toBeInTheDocument();
  expect(screen.getByLabelText("Attach file")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Send message" })).toBeInTheDocument();
});

it("renders expected artifacts and progress without exposing hidden reasoning", async () => {
  render(await ProjectPage({ params: Promise.resolve({ id: "demo" }) }));

  expect(screen.getByText("Evidence Map")).toBeInTheDocument();
  expect(screen.getByText("Gap Matrix")).toBeInTheDocument();
  expect(screen.getByText("Evaluating feasibility")).toBeInTheDocument();
  expect(screen.queryByText(/chain-of-thought/i)).not.toBeInTheDocument();
});
