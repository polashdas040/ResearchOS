import { render, screen } from "@testing-library/react";
import React from "react";
import RegisterPage from "./page";

it("renders the registration interface", () => {
  render(<RegisterPage />);

  expect(screen.getByRole("heading", { name: "Create your ResearchOS account" })).toBeInTheDocument();
  expect(screen.getByLabelText("Full name")).toBeInTheDocument();
  expect(screen.getByLabelText("Organization")).toBeInTheDocument();
  expect(screen.getByLabelText("Email")).toBeInTheDocument();
  expect(screen.getByLabelText("Password")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Create account" })).toBeInTheDocument();
});
