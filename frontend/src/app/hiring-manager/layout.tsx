"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, Search, Users, LogOut } from "lucide-react";
import { getToken, getStoredUser, logout, type AuthUser } from "@/lib/auth";

const NAV = [
  { href: "/hiring-manager", label: "Dashboard", icon: LayoutDashboard },
  { href: "/hiring-manager/search", label: "Search", icon: Search },
  { href: "/hiring-manager/candidates", label: "Candidates", icon: Users },
];

export default function HiringManagerLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);

  // Route guard: a hiring-manager / admin login is required to view this section.
  useEffect(() => {
    const stored = getStoredUser();
    // No token, or a non-HM token (e.g. a candidate signed in) → back to login.
    if (!getToken() || !stored || !["hiring_manager", "admin"].includes(stored.role)) {
      logout();
      router.replace("/login");
      return;
    }
    setUser(stored);
    setReady(true);
  }, [router]);

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-400">Checking your session…</p>
      </div>
    );
  }

  const displayName = user?.full_name || user?.email?.split("@")[0] || "Hiring Manager";
  const initials = (user?.full_name || user?.email || "HM")
    .split(/[\s@.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join("");

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="hidden lg:flex w-64 shrink-0 flex-col sticky top-0 h-screen bg-white border-r border-slate-200 px-5 py-8">
        <div className="flex items-center gap-3 mb-10 px-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl text-white text-sm font-bold shadow-md" style={{ background: "linear-gradient(135deg, #16a34a, #15803d)" }}>
            Z
          </div>
          <div>
            <p className="text-sm font-bold text-slate-800">ZennialPro</p>
            <p className="text-xs text-green-600 font-medium">Hiring Manager</p>
          </div>
        </div>

        <nav className="flex-1 flex flex-col gap-1">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-600 hover:bg-green-50 hover:text-green-700 transition-colors">
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>

        <div className="border-t border-slate-100 pt-4 mt-4">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center text-green-700 text-xs font-bold">{initials || "HM"}</div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-slate-700 truncate">{displayName}</p>
              <p className="text-[10px] text-slate-400 truncate" title={user?.email ?? ""}>{user?.email}</p>
            </div>
            <button onClick={handleLogout} title="Log out" className="text-slate-400 hover:text-red-600 transition-colors">
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between bg-white border-b border-slate-200 px-8">
          <div className="flex lg:hidden items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg text-white text-xs font-bold" style={{ background: "linear-gradient(135deg, #16a34a, #15803d)" }}>Z</div>
            <span className="text-sm font-bold text-slate-800">ZennialPro</span>
          </div>
          <div className="hidden lg:flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-sm text-slate-500 font-medium">Talent Pool</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/onboarding" className="text-xs text-slate-400 hover:text-slate-600 transition-colors">
              Candidate Portal →
            </Link>
            <button onClick={handleLogout} className="lg:hidden text-xs font-medium text-slate-500 hover:text-red-600">
              Log out
            </button>
          </div>
        </header>

        <main className="flex-1 px-8 py-8">
          {children}
        </main>
      </div>
    </div>
  );
}
