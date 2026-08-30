import React from "react";
import { HydrationSafeButton } from "./HydrationSafeControls";
import { artifacts } from "./workspace-data";

export function ArtifactPanel() {
  return (
    <aside
      aria-label="Artifacts"
      className="border-t border-[#d7dde6] bg-[#f7f9fb] p-4 lg:border-l lg:border-t-0"
    >
      <h2 className="text-sm font-semibold">Artifacts</h2>
      <div className="mt-3 space-y-2">
        {artifacts.map((artifact) => (
          <HydrationSafeButton
            key={artifact.title}
            type="button"
            className="flex w-full items-center justify-between gap-3 rounded border border-[#d7dde6] bg-white px-3 py-3 text-left text-sm hover:border-[#9fb0c2]"
          >
            <span className="min-w-0">
              <span className="block truncate font-medium">{artifact.title}</span>
              <span className="block truncate text-xs text-[#667386]">{artifact.artifactType}</span>
            </span>
            <span className="shrink-0 text-xs text-[#667386]">{artifact.version}</span>
          </HydrationSafeButton>
        ))}
      </div>
    </aside>
  );
}
