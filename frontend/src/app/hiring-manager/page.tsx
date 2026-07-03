"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { Users, CheckCircle2, TrendingUp, Award, ArrowRight, Loader2 } from "lucide-react";

interface DashboardData {
  total_candidates: number;
  verified_candidates: number;
  avg_interview_score: number;
  l1_passed: number;
  domain_breakdown: { domain: string; count: number }[];
  recent_candidates: {
    candidate_ref: string;
    full_name: string;
    current_title: string;
    primary_domain: string;
    readiness_score: number | null;
    verification_status: string;
    created_at: string;
  }[];
}

export default function HiringManagerDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("hiring-manager/dashboard").json<DashboardData>()
      .then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="h-6 w-6 animate-spin text-green-600" />
    </div>
  );

  if (!data) return <p className="text-slate-500">Failed to load dashboard.</p>;

  const stats = [
    { label: "Total Candidates", value: data.total_candidates, icon: Users, color: "bg-blue-50 text-blue-600" },
    { label: "Verified", value: data.verified_candidates, icon: CheckCircle2, color: "bg-green-50 text-green-600" },
    { label: "Avg Interview Score", value: `${data.avg_interview_score}%`, icon: TrendingUp, color: "bg-violet-50 text-violet-600" },
    { label: "L1 Passed", value: data.l1_passed, icon: Award, color: "bg-amber-50 text-amber-600" },
  ];

  const maxDomain = Math.max(...data.domain_breakdown.map((d) => d.count), 1);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">Overview of your talent pool</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="bg-white rounded-2xl border border-slate-200 p-5 flex items-center gap-4">
            <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${s.color}`}>
              <s.icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{s.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Domain breakdown */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="text-sm font-semibold text-slate-700 mb-5">Candidates by Domain</h2>
          <div className="space-y-3">
            {data.domain_breakdown.length === 0 && (
              <p className="text-sm text-slate-400">No data yet</p>
            )}
            {data.domain_breakdown.map((d) => (
              <div key={d.domain}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-medium text-slate-700">{d.domain}</span>
                  <span className="text-slate-500">{d.count}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-green-500 transition-all"
                    style={{ width: `${(d.count / maxDomain) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent candidates */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-semibold text-slate-700">Recent Candidates</h2>
            <Link href="/hiring-manager/candidates" className="text-xs text-green-600 hover:text-green-700 font-medium flex items-center gap-1">
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="space-y-3">
            {data.recent_candidates.length === 0 && (
              <p className="text-sm text-slate-400">No candidates yet</p>
            )}
            {data.recent_candidates.map((c) => (
              <Link key={c.candidate_ref} href={`/hiring-manager/candidates/${c.candidate_ref}`}
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors group">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-green-100 text-green-700 text-sm font-bold">
                  {c.full_name.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-800 truncate">{c.full_name}</p>
                  <p className="text-xs text-slate-500 truncate">{c.current_title || c.primary_domain || "—"}</p>
                </div>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                  c.verification_status === "VERIFIED"
                    ? "bg-green-100 text-green-700"
                    : "bg-slate-100 text-slate-500"
                }`}>
                  {c.verification_status}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 gap-4">
        <Link href="/hiring-manager/search"
          className="flex items-center gap-4 bg-green-600 hover:bg-green-700 text-white rounded-2xl p-6 transition-colors">
          <div className="flex-1">
            <p className="font-semibold text-base">Search Candidates</p>
            <p className="text-sm text-green-200 mt-1">Upload JD or enter required skills</p>
          </div>
          <ArrowRight className="h-5 w-5" />
        </Link>
        <Link href="/hiring-manager/candidates"
          className="flex items-center gap-4 bg-white hover:bg-slate-50 border border-slate-200 text-slate-800 rounded-2xl p-6 transition-colors">
          <div className="flex-1">
            <p className="font-semibold text-base">Browse Talent Pool</p>
            <p className="text-sm text-slate-500 mt-1">Filter by domain, score & skills</p>
          </div>
          <ArrowRight className="h-5 w-5" />
        </Link>
      </div>
    </div>
  );
}
