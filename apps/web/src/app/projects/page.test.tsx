import { render, screen } from "@testing-library/react";
import React from "react";
import ProjectsPage from "./page";

it("renders the projects shell", () => {
  render(<ProjectsPage />);

  expect(screen.getByRole("heading", { name: "Projects" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "New project" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /ADNI Literature Review/ })).toHaveAttribute(
    "href",
    "/project/demo"
  );
  expect(screen.getByText("3 active research workspaces")).toBeInTheDocument();
});
