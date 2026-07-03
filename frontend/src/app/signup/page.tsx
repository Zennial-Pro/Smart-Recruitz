"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { HTTPError } from "ky";
import { signup } from "@/lib/auth";

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await signup(email.trim(), password, fullName.trim() || undefined);
      router.push("/hiring-manager");
    } catch (err) {
      let msg = "Sign-up failed. Please try again.";
      if (err instanceof HTTPError) {
        try {
          const body = (await err.response.json()) as { detail?: string };
          if (body.detail) msg = body.detail;
        } catch {
          /* ignore */
        }
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl text-sm font-bold text-white shadow-md"
            style={{ background: "linear-gradient(135deg, #16a34a, #15803d)" }}
          >
            Z
          </div>
          <div>
            <p className="text-sm font-bold text-slate-800">SmartRecruitz</p>
            <p className="text-xs font-medium text-green-600">Create hiring-manager account</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-600">Full name</label>
            <input
              value={fullName} onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-green-400"
              placeholder="Jane Recruiter"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-600">Email</label>
            <input
              type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-green-400"
              placeholder="you@company.com"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-600">Password</label>
            <input
              type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-green-400"
              placeholder="At least 8 characters"
            />
          </div>

          {error && <p className="text-xs text-red-600">{error}</p>}

          <button
            type="submit" disabled={loading}
            className="w-full rounded-xl bg-green-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? "Creating…" : "Create account"}
          </button>
        </form>

        <p className="mt-5 text-center text-xs text-slate-500">
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-green-700 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
