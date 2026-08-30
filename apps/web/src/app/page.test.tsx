import { render, screen } from "@testing-library/react";
import React from "react";
import Page from "./page";

it("renders the ResearchOS workspace entry page", () => {
  render(<Page />);

  expect(screen.getByRole("heading", { name: "ResearchOS" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Open workspace" })).toHaveAttribute(
    "href",
    "/project/demo"
  );
  expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/login");
});
