import { render, screen } from "@testing-library/react";
import React from "react";
import LoginPage from "./page";

it("renders the login interface", () => {
  render(<LoginPage />);

  expect(screen.getByRole("heading", { name: "Sign in to ResearchOS" })).toBeInTheDocument();
  expect(screen.getByLabelText("Email")).toBeInTheDocument();
  expect(screen.getByLabelText("Password")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Create account" })).toHaveAttribute(
    "href",
    "/register"
  );
});
