import Link from "next/link";
import React from "react";

export function AppHeader() {
  return (
    <header className="flex min-h-16 flex-wrap items-center justify-between gap-3 border-b border-[#d7dde6] bg-white px-4 py-3 md:px-6">
      <Link href="/projects" className="min-w-0">
        <span className="block text-lg font-semibold text-[#172026]">ResearchOS</span>
        <span className="block text-xs text-[#647284]">
          Evidence-first autonomous research workspace
        </span>
      </Link>
      <nav aria-label="Account" className="flex items-center gap-2 text-sm">
        <Link className="rounded border border-[#c5cfda] px-3 py-2 font-medium" href="/billing">
          Credits: 1,240
        </Link>
        <Link className="rounded border border-[#c5cfda] px-3 py-2 font-medium" href="/settings">
          Settings
        </Link>
      </nav>
    </header>
  );
}
