import React from "react";
import RootLayout from "./layout";

it("suppresses hydration warnings from browser extensions on the document body", () => {
  const layout = RootLayout({ children: <main /> });
  const body = React.Children.toArray(layout.props.children)[0] as React.ReactElement<{
    suppressHydrationWarning?: boolean;
  }>;

  expect(body.props.suppressHydrationWarning).toBe(true);
});
