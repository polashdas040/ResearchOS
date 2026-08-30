import Link from "next/link";
import React from "react";

export default function Page() {
  return (
    <main className="min-h-screen bg-[#eef2f5] text-[#172026]">
      <section className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-12">
        <p className="text-sm font-medium text-[#176b5b]">ResearchOS</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-normal md:text-6xl">ResearchOS</h1>
        <p className="mt-5 max-w-2xl text-base leading-7 text-[#536174] md:text-lg">
          A research workspace for persistent projects, streaming scientific chat, evidence
          artifacts, and reproducible research runs.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/project/demo"
            className="rounded bg-[#176b5b] px-4 py-2.5 text-sm font-semibold text-white"
          >
            Open workspace
          </Link>
          <Link
            href="/login"
            className="rounded border border-[#b7c2cf] bg-white px-4 py-2.5 text-sm font-semibold"
          >
            Sign in
          </Link>
        </div>
      </section>
    </main>
  );
}
