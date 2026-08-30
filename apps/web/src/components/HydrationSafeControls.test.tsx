import React from "react";
import { HydrationSafeButton, HydrationSafeInput } from "./HydrationSafeControls";

it("suppresses hydration warnings on controls commonly mutated by browser extensions", () => {
  const button = HydrationSafeButton({ children: "Send", type: "button" });
  const input = HydrationSafeInput({ "aria-label": "Prompt" });

  expect(button.props.suppressHydrationWarning).toBe(true);
  expect(input.props.suppressHydrationWarning).toBe(true);
});
