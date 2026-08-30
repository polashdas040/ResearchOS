import React from "react";
import { AppHeader } from "../../components/AppHeader";
import { HydrationSafeButton } from "../../components/HydrationSafeControls";

export default function BillingPage() {
  return (
    <main className="min-h-screen bg-[#eef2f5] text-[#172026]">
      <AppHeader />
      <section className="mx-auto max-w-5xl px-4 py-8 md:px-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Billing</h1>
            <p className="mt-1 text-sm text-[#536174]">1,240 credits</p>
          </div>
          <HydrationSafeButton
            type="button"
            className="rounded bg-[#176b5b] px-4 py-2.5 text-sm font-semibold text-white"
          >
            Add credits
          </HydrationSafeButton>
        </div>
        <section className="mt-6 rounded border border-[#d7dde6] bg-white p-5">
          <h2 className="text-base font-semibold">Usage this month</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <Metric label="Streaming chat" value="182 credits" />
            <Metric label="Model usage events" value="37" />
            <Metric label="Reserved budget" value="0 credits" />
          </div>
        </section>
      </section>
    </main>
  );
}

type MetricProps = {
  label: string;
  value: string;
};

function Metric({ label, value }: MetricProps) {
  return (
    <div className="rounded border border-[#d7dde6] bg-[#f8fafc] p-4">
      <p className="text-sm text-[#536174]">{label}</p>
      <p className="mt-2 text-lg font-semibold">{value}</p>
    </div>
  );
}
