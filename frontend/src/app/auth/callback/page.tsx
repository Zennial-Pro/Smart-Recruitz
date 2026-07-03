"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { applyToken } from "@/lib/auth";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const next = params.get("next") || "/hiring-manager";
    if (!token) {
      router.replace("/login?error=google");
      return;
    }
    applyToken(token).then((user) => {
      router.replace(user ? next : "/login?error=google");
    });
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <p className="text-sm text-slate-400">Signing you in…</p>
    </div>
  );
}
