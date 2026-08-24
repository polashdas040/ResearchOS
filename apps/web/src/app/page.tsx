import React from "react";

const projects = [
  { name: "ADNI Literature Review", status: "Active", accent: "bg-emerald-500" },
  { name: "Glioma Imaging Cohort", status: "Draft", accent: "bg-sky-500" },
  { name: "Transformer Survey", status: "Paused", accent: "bg-amber-500" }
];

const runSteps = [
  "Dataset analyzed",
  "43 papers retrieved",
  "17 papers selected",
  "6 research gaps",
  "Evaluating feasibility"
];

const artifacts = ["Evidence Map", "Gap Matrix", "Dataset Profile", "Hypothesis Set"];

export default function Page() {
  return (
    <div className="min-h-screen bg-[#f6f7f9] text-[#172026]">
      <section className="flex min-h-screen flex-col">
        <header className="flex min-h-16 items-center justify-between border-b border-[#d8dee8] bg-white px-5">
          <div>
            <h1 className="text-xl font-semibold tracking-normal">ResearchOS</h1>
            <p className="text-xs text-[#627084]">Evidence-first autonomous research workspace</p>
          </div>
          <div className="hidden items-center gap-3 text-sm text-[#526174] md:flex">
            <span>Credits: 1,240</span>
            <button className="rounded border border-[#c8d0dc] px-3 py-1.5 text-sm font-medium">
              Settings
            </button>
          </div>
        </header>

        <div className="grid flex-1 grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)_320px]">
          <nav
            aria-label="Projects"
            className="border-b border-[#d8dee8] bg-[#fbfcfd] p-4 lg:border-b-0 lg:border-r"
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Projects</h2>
              <button className="h-8 w-8 rounded border border-[#c8d0dc] text-lg leading-none">+</button>
            </div>
            <div className="space-y-2">
              {projects.map((project) => (
                <button
                  key={project.name}
                  className="flex w-full items-start gap-3 rounded border border-transparent px-3 py-3 text-left hover:border-[#c8d0dc] hover:bg-white"
                >
                  <span className={`mt-1 h-2.5 w-2.5 rounded-full ${project.accent}`} />
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium">{project.name}</span>
                    <span className="block text-xs text-[#6b7788]">{project.status}</span>
                  </span>
                </button>
              ))}
            </div>
          </nav>

          <main aria-label="Research chat" className="flex min-h-[640px] flex-col bg-white">
            <div className="border-b border-[#d8dee8] px-5 py-4">
              <p className="text-xs font-medium uppercase text-[#6b7788]">Current run</p>
              <h2 className="mt-1 text-lg font-semibold">Biomarker evidence synthesis</h2>
            </div>

            <div className="flex-1 space-y-5 overflow-y-auto px-5 py-6">
              <article className="max-w-3xl">
                <p className="mb-2 text-xs font-medium text-[#6b7788]">Researcher</p>
                <div className="rounded border border-[#d8dee8] bg-[#f8fafc] p-4 text-sm leading-6">
                  Map evidence for hippocampal atrophy biomarkers.
                </div>
              </article>

              <article className="ml-auto max-w-3xl">
                <p className="mb-2 text-xs font-medium text-[#6b7788]">ResearchOS</p>
                <div className="rounded border border-[#c7d8ca] bg-[#f6fbf7] p-4 text-sm leading-6">
                  I found converging evidence across longitudinal MRI studies, but the strongest
                  claims need citation validation before final wording.
                </div>
              </article>

              <section className="grid gap-3 md:grid-cols-3">
                <div className="rounded border border-[#d8dee8] bg-[#fbfcfd] p-3">
                  <p className="text-xs text-[#6b7788]">Sources</p>
                  <p className="mt-1 text-lg font-semibold">17</p>
                </div>
                <div className="rounded border border-[#d8dee8] bg-[#fbfcfd] p-3">
                  <p className="text-xs text-[#6b7788]">Claims</p>
                  <p className="mt-1 text-lg font-semibold">24</p>
                </div>
                <div className="rounded border border-[#d8dee8] bg-[#fbfcfd] p-3">
                  <p className="text-xs text-[#6b7788]">Warnings</p>
                  <p className="mt-1 text-lg font-semibold text-[#9a5b00]">3</p>
                </div>
              </section>
            </div>

            <form className="border-t border-[#d8dee8] bg-[#fbfcfd] p-4">
              <div className="flex items-center gap-3 rounded border border-[#b9c4d2] bg-white p-2">
                <button
                  type="button"
                  className="h-9 rounded border border-[#d8dee8] px-3 text-sm font-medium"
                >
                  Attach
                </button>
                <input
                  className="min-w-0 flex-1 bg-transparent px-2 text-sm outline-none"
                  placeholder="Ask ResearchOS..."
                />
                <button
                  type="submit"
                  className="h-9 rounded bg-[#1f6f5b] px-4 text-sm font-semibold text-white"
                >
                  Send
                </button>
              </div>
            </form>
          </main>

          <aside
            aria-label="Artifacts and run status"
            className="border-t border-[#d8dee8] bg-[#fbfcfd] p-4 lg:border-l lg:border-t-0"
          >
            <section>
              <h2 className="text-sm font-semibold">Research Run</h2>
              <ol className="mt-3 space-y-2">
                {runSteps.map((step, index) => (
                  <li key={step} className="flex items-center gap-2 text-sm">
                    <span
                      className={`h-2.5 w-2.5 rounded-full ${
                        index === runSteps.length - 1 ? "bg-amber-500" : "bg-emerald-500"
                      }`}
                    />
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </section>

            <section className="mt-8">
              <h2 className="text-sm font-semibold">Artifacts</h2>
              <div className="mt-3 space-y-2">
                {artifacts.map((artifact) => (
                  <button
                    key={artifact}
                    className="flex w-full items-center justify-between rounded border border-[#d8dee8] bg-white px-3 py-3 text-left text-sm hover:border-[#9fb0c2]"
                  >
                    <span>{artifact}</span>
                    <span className="text-xs text-[#6b7788]">v1</span>
                  </button>
                ))}
              </div>
            </section>
          </aside>
        </div>
      </section>
    </div>
  );
}
