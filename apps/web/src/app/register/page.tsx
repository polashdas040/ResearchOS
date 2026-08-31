"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import React from "react";
import { HydrationSafeButton, HydrationSafeInput } from "../../components/HydrationSafeControls";
import { register } from "../../lib/api-client";

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    const form = new FormData(event.currentTarget);
    try {
      await register({
        email: String(form.get("email")),
        password: String(form.get("password")),
        fullName: String(form.get("full-name")),
        organizationName: String(form.get("organization"))
      });
      router.push("/projects");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Registration failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#eef2f5] px-4 py-10 text-[#172026]">
      <section className="w-full max-w-lg rounded border border-[#d7dde6] bg-white p-6">
        <h1 className="text-2xl font-semibold">Create your ResearchOS account</h1>
        <form className="mt-6 grid gap-4" onSubmit={handleSubmit}>
          <Field id="full-name" label="Full name" type="text" />
          <Field id="organization" label="Organization" type="text" />
          <Field id="email" label="Email" type="email" />
          <Field id="password" label="Password" type="password" minLength={12} />
          <HydrationSafeButton
            type="submit"
            disabled={isSubmitting}
            className="h-11 rounded bg-[#176b5b] font-semibold text-white"
          >
            {isSubmitting ? "Creating account..." : "Create account"}
          </HydrationSafeButton>
        </form>
        {error ? <p className="mt-4 text-sm font-medium text-[#a33a2d]">{error}</p> : null}
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
  minLength?: number;
};

function Field({ id, label, type, minLength }: FieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium" htmlFor={id}>
        {label}
      </label>
      <HydrationSafeInput
        id={id}
        name={id}
        type={type}
        minLength={minLength}
        className="mt-2 h-11 w-full rounded border border-[#b7c2cf] px-3 text-sm"
      />
    </div>
  );
}
