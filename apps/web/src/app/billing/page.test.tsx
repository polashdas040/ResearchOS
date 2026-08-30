import { render, screen } from "@testing-library/react";
import React from "react";
import BillingPage from "./page";

it("renders billing and credit status", () => {
  render(<BillingPage />);

  expect(screen.getByRole("heading", { name: "Billing" })).toBeInTheDocument();
  expect(screen.getByText("1,240 credits")).toBeInTheDocument();
  expect(screen.getByText("Usage this month")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Add credits" })).toBeInTheDocument();
});
