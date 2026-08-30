import React from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement>;
type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export function HydrationSafeButton(props: ButtonProps) {
  return <button suppressHydrationWarning {...props} />;
}

export function HydrationSafeInput(props: InputProps) {
  return <input suppressHydrationWarning {...props} />;
}
