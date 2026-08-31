"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import React from "react";
import { HydrationSafeButton, HydrationSafeInput } from "../../components/HydrationSafeControls";
import { login } from "../../lib/api-client";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    const form = new FormData(event.currentTarget);
    try {
      await login(String(form.get("email")), String(form.get("password")));
      router.push("/projects");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Sign in failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#eef2f5] px-4 py-10 text-[#172026]">
      <section className="w-full max-w-md rounded border border-[#d7dde6] bg-white p-6">
        <h1 className="text-2xl font-semibold">Sign in to ResearchOS</h1>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm font-medium" htmlFor="email">
            Email
          </label>
          <HydrationSafeInput
            id="email"
            name="email"
            type="email"
            className="h-11 w-full rounded border border-[#b7c2cf] px-3 text-sm"
          />
          <label className="block text-sm font-medium" htmlFor="password">
            Password
          </label>
          <HydrationSafeInput
            id="password"
            name="password"
            type="password"
            className="h-11 w-full rounded border border-[#b7c2cf] px-3 text-sm"
          />
          <HydrationSafeButton
            type="submit"
            disabled={isSubmitting}
            className="h-11 w-full rounded bg-[#176b5b] font-semibold text-white"
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </HydrationSafeButton>
        </form>
        {error ? <p className="mt-4 text-sm font-medium text-[#a33a2d]">{error}</p> : null}
        <p className="mt-5 text-sm text-[#536174]">
          New here?{" "}
          <Link href="/register" className="font-semibold text-[#176b5b]">
            Create account
          </Link>
        </p>
      </section>
    </main>
  );
}
