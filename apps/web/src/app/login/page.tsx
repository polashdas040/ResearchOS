import Link from "next/link";
import React from "react";
import { HydrationSafeButton, HydrationSafeInput } from "../../components/HydrationSafeControls";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#eef2f5] px-4 py-10 text-[#172026]">
      <section className="w-full max-w-md rounded border border-[#d7dde6] bg-white p-6">
        <h1 className="text-2xl font-semibold">Sign in to ResearchOS</h1>
        <form className="mt-6 space-y-4">
          <label className="block text-sm font-medium" htmlFor="email">
            Email
          </label>
          <HydrationSafeInput
            id="email"
            type="email"
            className="h-11 w-full rounded border border-[#b7c2cf] px-3 text-sm"
          />
          <label className="block text-sm font-medium" htmlFor="password">
            Password
          </label>
          <HydrationSafeInput
            id="password"
            type="password"
            className="h-11 w-full rounded border border-[#b7c2cf] px-3 text-sm"
          />
          <HydrationSafeButton
            type="submit"
            className="h-11 w-full rounded bg-[#176b5b] font-semibold text-white"
          >
            Sign in
          </HydrationSafeButton>
        </form>
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
