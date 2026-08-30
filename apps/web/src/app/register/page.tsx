import Link from "next/link";
import React from "react";
import { HydrationSafeButton, HydrationSafeInput } from "../../components/HydrationSafeControls";

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#eef2f5] px-4 py-10 text-[#172026]">
      <section className="w-full max-w-lg rounded border border-[#d7dde6] bg-white p-6">
        <h1 className="text-2xl font-semibold">Create your ResearchOS account</h1>
        <form className="mt-6 grid gap-4">
          <Field id="full-name" label="Full name" type="text" />
          <Field id="organization" label="Organization" type="text" />
          <Field id="email" label="Email" type="email" />
          <Field id="password" label="Password" type="password" />
          <HydrationSafeButton
            type="submit"
            className="h-11 rounded bg-[#176b5b] font-semibold text-white"
          >
            Create account
          </HydrationSafeButton>
        </form>
        <Link href="/login" className="mt-5 inline-block text-sm font-semibold text-[#176b5b]">
          Sign in
        </Link>
      </section>
    </main>
  );
}

type FieldProps = {
  id: string;
  label: string;
  type: string;
};

function Field({ id, label, type }: FieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium" htmlFor={id}>
        {label}
      </label>
      <HydrationSafeInput
        id={id}
        type={type}
        className="mt-2 h-11 w-full rounded border border-[#b7c2cf] px-3 text-sm"
      />
    </div>
  );
}
