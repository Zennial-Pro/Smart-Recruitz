"use client";

import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { OnboardingSteps } from "@/components/chat/onboarding-steps";
import { RestartButton } from "@/components/chat/restart-button";
import { getToken, getStoredUser, logout, type AuthUser } from "@/lib/auth";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const CANDIDATE_LOGIN_URL = `${API_BASE}/auth/google?intent=candidate`;

function CandidateSignIn() {
  return (
    <div
      className="flex min-h-screen items-center justify-center px-4"
      style={{ background: "linear-gradient(135deg, #f5f3ff 0%, #ede9fe 30%, #f0f4ff 70%, #e8f0fe 100%)" }}
    >
      <div className="w-full max-w-sm rounded-2xl border border-violet-100 bg-white p-8 shadow-sm text-center">
        <div className="mb-6 flex items-center justify-center gap-3">
          <div
            className="flex h-11 w-11 items-center justify-center rounded-2xl text-sm font-bold text-white shadow-lg"
            style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}
          >
            SR
          </div>
          <div className="text-left">
            <p className="text-base font-bold text-slate-800">SmartRecruitz</p>
            <p className="text-xs font-medium text-violet-500">Candidate Portal</p>
          </div>
        </div>
        <p className="mb-6 text-sm text-slate-500">Sign in to start your verification.</p>
        <a
          href={CANDIDATE_LOGIN_URL}
          className="flex w-full items-center justify-center gap-3 rounded-xl border border-slate-200 bg-white py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-50"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.27-4.74 3.27-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.1a6.6 6.6 0 0 1 0-4.2V7.06H2.18a11 11 0 0 0 0 9.88l3.66-2.84z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z"/>
          </svg>
          Continue with Google
        </a>
      </div>
    </div>
  );
}

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  const [authState, setAuthState] = useState<"checking" | "in" | "out">("checking");
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const token = getToken();
    setUser(token ? getStoredUser() : null);
    setAuthState(token ? "in" : "out");
  }, []);

  function handleLogout() {
    logout();
    setAuthState("out");
  }

  if (authState === "checking") {
    return (
      <div
        className="flex min-h-screen items-center justify-center"
        style={{ background: "linear-gradient(135deg, #f5f3ff 0%, #ede9fe 30%, #f0f4ff 70%, #e8f0fe 100%)" }}
      >
        <p className="text-sm text-slate-400">Loading…</p>
      </div>
    );
  }

  if (authState === "out") {
    return <CandidateSignIn />;
  }

  const displayName = user?.full_name || user?.email?.split("@")[0] || "Candidate";
  const initials = (user?.full_name || user?.email || "You")
    .split(/[\s@.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join("");

  return (
    <div className="flex min-h-screen" style={{ background: "linear-gradient(135deg, #f5f3ff 0%, #ede9fe 30%, #f0f4ff 70%, #e8f0fe 100%)" }}>

      {/* Left sidebar — sticky */}
      <aside className="hidden lg:flex w-72 shrink-0 flex-col sticky top-0 h-screen bg-white/60 backdrop-blur-xl border-r border-violet-100 px-6 py-10 overflow-y-auto">
        <div className="flex items-center gap-3.5 mb-12 px-2">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl text-white text-sm font-bold shadow-lg" style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}>
            SR
          </div>
          <div>
            <p className="text-base font-bold leading-tight text-slate-800">SmartRecruitz</p>
            <p className="text-xs text-violet-500 font-medium">Candidate Portal</p>
          </div>
        </div>

        <div className="flex-1">
          <p className="text-[11px] font-semibold uppercase tracking-widest text-violet-400 px-2 mb-4">Your Journey</p>
          <OnboardingSteps />
        </div>

        {user && (
          <div className="border-t border-violet-100 pt-4 mt-4">
            <div className="flex items-center gap-3 px-2">
              <div className="h-9 w-9 shrink-0 rounded-full bg-violet-100 flex items-center justify-center text-violet-700 text-xs font-bold">{initials || "You"}</div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-slate-700 truncate">{displayName}</p>
                <p className="text-[10px] text-slate-400 truncate" title={user.email}>{user.email}</p>
              </div>
            </div>
          </div>
        )}

      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col">

        {/* Header — sticky */}
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between bg-white/50 backdrop-blur-xl border-b border-violet-100/60 px-8">
          <div className="flex lg:hidden items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl text-white text-xs font-bold" style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}>SR</div>
            <span className="text-sm font-bold text-slate-800">SmartRecruitz</span>
          </div>
          <div className="hidden lg:flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-sm text-slate-500 font-medium">Candidate verification</span>
          </div>
          <div className="flex items-center gap-3">
            <RestartButton />
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:bg-red-50 hover:text-red-600"
            >
              <LogOut className="h-3.5 w-3.5" />
              Log out
            </button>
          </div>
        </header>

        {/* Chat content — full page scroll */}
        <main className="flex-1">
          <div className="mx-auto max-w-5xl w-full px-10 py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
