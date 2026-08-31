import { render, screen } from "@testing-library/react";
import React from "react";
import ProjectsPage from "./page";

it("renders the projects shell", () => {
  render(<ProjectsPage />);

  expect(screen.getByRole("heading", { name: "Projects" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "New project" })).toBeInTheDocument();
  expect(screen.getByText("0 research workspaces")).toBeInTheDocument();
  expect(screen.getByText("Please sign in or create an account first.")).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /ADNI Literature Review/ })).not.toBeInTheDocument();
});
