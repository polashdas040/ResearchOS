import React from "react";
import { AppHeader } from "../../components/AppHeader";
import { HydrationSafeButton, HydrationSafeInput } from "../../components/HydrationSafeControls";

export default function SettingsPage() {
  return (
    <main className="min-h-screen bg-[#eef2f5] text-[#172026]">
      <AppHeader />
      <section className="mx-auto max-w-3xl px-4 py-8 md:px-6">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <form className="mt-6 rounded border border-[#d7dde6] bg-white p-5">
          <label className="block text-sm font-medium" htmlFor="display-name">
            Display name
          </label>
          <HydrationSafeInput
            id="display-name"
            className="mt-2 h-11 w-full rounded border border-[#b7c2cf] px-3 text-sm"
            defaultValue="Research User"
          />
          <label
            className="mt-5 flex items-center gap-3 text-sm font-medium"
            htmlFor="email-notifications"
          >
            <HydrationSafeInput
              id="email-notifications"
              type="checkbox"
              className="h-4 w-4"
              defaultChecked
            />
            Email notifications
          </label>
          <HydrationSafeButton
            type="submit"
            className="mt-6 rounded bg-[#176b5b] px-4 py-2.5 text-sm font-semibold text-white"
          >
            Save settings
          </HydrationSafeButton>
        </form>
      </section>
    </main>
  );
}
