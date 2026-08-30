import { render, screen } from "@testing-library/react";
import React from "react";
import SettingsPage from "./page";

it("renders account and workspace settings", () => {
  render(<SettingsPage />);

  expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
  expect(screen.getByLabelText("Display name")).toBeInTheDocument();
  expect(screen.getByLabelText("Email notifications")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Save settings" })).toBeInTheDocument();
});
