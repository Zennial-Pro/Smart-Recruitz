"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { CheckCircle2, Loader2, SlidersHorizontal, X, Linkedin, Github, FileText, Building2 } from "lucide-react";

interface CandidateCard {
  candidate_ref: string;
  full_name: string;
  current_title: string | null;
  primary_domain: string | null;
  total_experience_years: number | null;
  overall_score: number | null;
  resume_overall_score: number | null;
  l1_status: string | null;
  top_skills: string[];
  verification_status: string;
  location: string | null;
  github_url: string | null;
  linkedin_url: string | null;
  current_ctc: string | null;
  expected_ctc: string | null;
  notice_period: string | null;
  working_status: string | null;
  preferred_location: string | null;
  product_experience_years: number | null;
  service_experience_years: number | null;
  gcc_experience_years: number | null;
  startup_experience_years: number | null;
  dominant_company_type: string | null;
  created_at: string;
}

const COMPANY_TYPE_TONE: Record<string, string> = {
  PRODUCT: "bg-emerald-100 text-emerald-700 border-emerald-200",
  SERVICE: "bg-amber-100 text-amber-700 border-amber-200",
  GCC: "bg-sky-100 text-sky-700 border-sky-200",
  STARTUP: "bg-violet-100 text-violet-700 border-violet-200",
  OTHER: "bg-slate-100 text-slate-600 border-slate-200",
};
const COMPANY_TYPE_LABEL: Record<string, string> = {
  PRODUCT: "Product",
  SERVICE: "Service",
  GCC: "GCC",
  STARTUP: "Startup",
  OTHER: "Other",
};

function scoreTone(score: number | null | undefined): string {
  if (score == null) return "bg-slate-100 text-slate-500";
  if (score >= 85) return "bg-green-100 text-green-700";
  if (score >= 70) return "bg-emerald-100 text-emerald-700";
  if (score >= 50) return "bg-amber-100 text-amber-700";
  return "bg-red-100 text-red-600";
}

const DOMAINS = ["AI/ML", "Backend", "Frontend", "Full Stack", "DevOps", "Data", "Mobile", "Security"];
const L1_OPTIONS = [{ label: "All", value: "" }, { label: "Passed", value: "PASSED" }, { label: "Failed", value: "FAILED" }];

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<CandidateCard[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [domain, setDomain] = useState("");
  const [minScore, setMinScore] = useState("");
  const [minResumeScore, setMinResumeScore] = useState("");
  const [minExp, setMinExp] = useState("");
  const [minProductYears, setMinProductYears] = useState("");
  const [companyTypeFilter, setCompanyTypeFilter] = useState("");
  const [l1Status, setL1Status] = useState("");
  const [search, setSearch] = useState("");
  const [skills, setSkills] = useState("");

  const fetchCandidates = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (domain) params.set("domain", domain);
    if (minScore) params.set("min_score", minScore);
    if (minResumeScore) params.set("min_resume_score", minResumeScore);
    if (minExp) params.set("min_experience", minExp);
    if (minProductYears) params.set("min_product_years", minProductYears);
    if (companyTypeFilter) params.set("company_type", companyTypeFilter);
    if (l1Status) params.set("l1_status", l1Status);
    if (search) params.set("search", search);
    if (skills) params.set("skills", skills);
    try {
      const res = await api.get(`hiring-manager/candidates?${params}`).json<{ total: number; candidates: CandidateCard[] }>();
      setCandidates(res.candidates);
      setTotal(res.total);
    } finally {
      setLoading(false);
    }
  }, [domain, minScore, minResumeScore, minExp, minProductYears, companyTypeFilter, l1Status, search, skills]);

  useEffect(() => { fetchCandidates(); }, [fetchCandidates]);

  function clearFilters() {
    setDomain(""); setMinScore(""); setMinResumeScore(""); setMinExp("");
    setMinProductYears(""); setCompanyTypeFilter("");
    setL1Status(""); setSearch(""); setSkills("");
  }

  const hasFilters = !!(domain || minScore || minResumeScore || minExp || minProductYears || companyTypeFilter || l1Status || search || skills);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Talent Pool</h1>
          <p className="text-sm text-slate-500 mt-1">{total} candidate{total !== 1 ? "s" : ""} found</p>
        </div>
        {hasFilters && (
          <button onClick={clearFilters} className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 border border-slate-200 rounded-lg px-3 py-1.5 transition-colors">
            <X className="h-3.5 w-3.5" /> Clear filters
          </button>
        )}
      </div>

      {/* Filters bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          <SlidersHorizontal className="h-3.5 w-3.5" /> Filters
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <input
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-green-400 transition-colors"
            placeholder="Search name or title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-green-400 transition-colors bg-white"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
          >
            <option value="">All Domains</option>
            {DOMAINS.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
          <select
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-green-400 transition-colors bg-white"
            value={l1Status}
            onChange={(e) => setL1Status(e.target.value)}
          >
            {L1_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label} L1</option>)}
          </select>
          <input
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-green-400 transition-colors"
            placeholder="Min L1 score"
            type="number"
            value={minScore}
            onChange={(e) => setMinScore(e.target.value)}
          />
          <input
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-green-400 transition-colors"
            placeholder="Min resume score"
            type="number"
            value={minResumeScore}
            onChange={(e) => setMinResumeScore(e.target.value)}
          />
          <input
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-green-400 transition-colors"
            placeholder="Min experience (years)"
            type="number"
            value={minExp}
            onChange={(e) => setMinExp(e.target.value)}
          />
          <input
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-emerald-400 transition-colors"
            placeholder="Min product-co years"
            type="number"
            value={minProductYears}
            onChange={(e) => setMinProductYears(e.target.value)}
          />
          <select
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-emerald-400 transition-colors bg-white"
            value={companyTypeFilter}
            onChange={(e) => setCompanyTypeFilter(e.target.value)}
          >
            <option value="">Any company type</option>
            <option value="PRODUCT">Product</option>
            <option value="SERVICE">Service</option>
            <option value="GCC">GCC</option>
            <option value="STARTUP">Startup</option>
          </select>
          <input
            className="col-span-2 lg:col-span-3 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-green-400 transition-colors"
            placeholder="Filter by skills (comma-separated, e.g. React, Python, AWS)"
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
          />
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-green-600" />
        </div>
      ) : candidates.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <p className="text-slate-400 text-sm">No candidates match your filters.</p>
        </div>
      ) : (
        <div className="grid lg:grid-cols-2 gap-4">
          {candidates.map((c) => {
            const passed = c.l1_status === "PASSED";
            return (
              <Link key={c.candidate_ref} href={`/hiring-manager/candidates/${c.candidate_ref}`}
                className="bg-white rounded-2xl border border-slate-200 hover:border-green-300 hover:shadow-md transition-all p-5 space-y-4 block">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-green-100 text-green-700 text-base font-bold">
                      {c.full_name.charAt(0)}
                    </div>
                    <div className="min-w-0">
                      <p className="font-semibold text-slate-800 truncate">{c.full_name}</p>
                      <p className="text-xs text-slate-500 truncate">{c.current_title || c.primary_domain || "—"}</p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    {c.overall_score !== null && (
                      <span className={`text-sm font-bold px-3 py-1 rounded-full ${passed ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"}`}>
                        L1 {c.overall_score}%
                      </span>
                    )}
                    {c.resume_overall_score !== null && c.resume_overall_score !== undefined && (
                      <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full inline-flex items-center gap-1 ${scoreTone(c.resume_overall_score)}`}>
                        <FileText className="h-3 w-3" /> Resume {Math.round(c.resume_overall_score)}
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="rounded-lg bg-slate-50 p-2">
                    <p className="font-semibold text-slate-800">{c.total_experience_years ? `${c.total_experience_years}y` : "—"}</p>
                    <p className="text-slate-500">Exp</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-2">
                    <p className="font-semibold text-slate-800 truncate">{c.primary_domain || "—"}</p>
                    <p className="text-slate-500">Domain</p>
                  </div>
                  <div className={`rounded-lg p-2 ${c.l1_status ? (passed ? "bg-green-50" : "bg-red-50") : "bg-slate-50"}`}>
                    <p className={`font-semibold text-xs ${c.l1_status ? (passed ? "text-green-700" : "text-red-600") : "text-slate-800"}`}>
                      {c.l1_status || "No L1"}
                    </p>
                    <p className="text-slate-500">L1</p>
                  </div>
                </div>

                {/* Company-orientation summary */}
                {(c.dominant_company_type || c.product_experience_years || c.service_experience_years) && (
                  <div className="flex flex-wrap gap-1.5 items-center text-[11px]">
                    {c.dominant_company_type && (
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold border ${COMPANY_TYPE_TONE[c.dominant_company_type] ?? COMPANY_TYPE_TONE.OTHER}`}>
                        <Building2 className="h-3 w-3" />
                        {COMPANY_TYPE_LABEL[c.dominant_company_type] ?? c.dominant_company_type}
                      </span>
                    )}
                    {(c.product_experience_years ?? 0) > 0 && (
                      <span className="text-emerald-700"><b>Product:</b> {c.product_experience_years}y</span>
                    )}
                    {(c.service_experience_years ?? 0) > 0 && (
                      <span className="text-amber-700"><b>Service:</b> {c.service_experience_years}y</span>
                    )}
                    {(c.gcc_experience_years ?? 0) > 0 && (
                      <span className="text-sky-700"><b>GCC:</b> {c.gcc_experience_years}y</span>
                    )}
                    {(c.startup_experience_years ?? 0) > 0 && (
                      <span className="text-violet-700"><b>Startup:</b> {c.startup_experience_years}y</span>
                    )}
                  </div>
                )}

                {(c.current_ctc || c.expected_ctc || c.notice_period || c.working_status || c.preferred_location) && (
                  <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-slate-500">
                    {c.current_ctc && <span><b className="text-slate-700">CTC:</b> {c.current_ctc}</span>}
                    {c.expected_ctc && <span><b className="text-slate-700">Expected:</b> {c.expected_ctc}</span>}
                    {c.notice_period && <span><b className="text-slate-700">Notice:</b> {c.notice_period}</span>}
                    {c.working_status && <span><b className="text-slate-700">Status:</b> {c.working_status}</span>}
                    {c.preferred_location && <span><b className="text-slate-700">Prefers:</b> {c.preferred_location}</span>}
                  </div>
                )}

                <div className="flex flex-wrap gap-1.5">
                  {c.top_skills.map((s) => (
                    <span key={s} className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-medium">{s}</span>
                  ))}
                </div>

                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-1.5">
                    {c.linkedin_url && (
                      <span className="inline-flex items-center gap-1 text-[10px] bg-sky-50 text-sky-700 border border-sky-100 rounded-full px-2 py-0.5">
                        <Linkedin className="h-3 w-3" /> LinkedIn
                      </span>
                    )}
                    {c.github_url && (
                      <span className="inline-flex items-center gap-1 text-[10px] bg-slate-50 text-slate-700 border border-slate-200 rounded-full px-2 py-0.5">
                        <Github className="h-3 w-3" /> GitHub
                      </span>
                    )}
                  </div>
                  {c.verification_status === "VERIFIED" && (
                    <div className="flex items-center gap-1 text-xs text-green-600 font-medium">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Verified
                    </div>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
