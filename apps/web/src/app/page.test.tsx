import { render, screen } from "@testing-library/react";
import React from "react";
import Page from "./page";

it("renders the ResearchOS workspace interface", () => {
  render(<Page />);

  expect(screen.getByRole("heading", { name: "ResearchOS" })).toBeInTheDocument();
  expect(screen.getByRole("navigation", { name: "Projects" })).toBeInTheDocument();
  expect(screen.getByText("ADNI Literature Review")).toBeInTheDocument();
  expect(screen.getByRole("main", { name: "Research chat" })).toBeInTheDocument();
  expect(screen.getByText("Map evidence for hippocampal atrophy biomarkers.")).toBeInTheDocument();
  expect(screen.getByPlaceholderText("Ask ResearchOS...")).toBeInTheDocument();
  expect(screen.getByRole("complementary", { name: "Artifacts and run status" })).toBeInTheDocument();
  expect(screen.getByText("Evidence Map")).toBeInTheDocument();
  expect(screen.getByText("Evaluating feasibility")).toBeInTheDocument();
});
