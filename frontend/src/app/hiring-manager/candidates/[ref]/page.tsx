"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft, Loader2, CheckCircle2, XCircle, Trophy,
  Briefcase, GraduationCap, Star, Mail, Phone, MapPin, RefreshCw,
  FileText, Linkedin, Github, ShieldAlert, ShieldCheck, Award, Code2,
  Users, BookOpen, Sparkles, IndianRupee, Clock, Activity, Building2,
  ExternalLink, Video, MessageSquare, Trash2,
} from "lucide-react";

interface ResumeSubScores {
  skills_score: number;
  experience_score: number;
  education_score: number;
  value_add_score: number;
}
interface ResumeAnalytics {
  skill_count: number;
  avg_tenure_months: number;
  longest_tenure_months: number;
  employment_gap_months: number;
  job_count: number;
  education_level: string;
  top_domain: string;
  product_experience_years?: number;
  service_experience_years?: number;
  gcc_experience_years?: number;
  startup_experience_years?: number;
  dominant_company_type?: string;
}
interface ValueAddItem { category: string; description: string }
interface ResumeAnalysis {
  overall_score: number;
  summary: string;
  sub_scores: ResumeSubScores;
  analytics: ResumeAnalytics;
  value_add_items: ValueAddItem[];
}
interface ConsistencyMismatch { type: string; company: string; details: string }
interface LinkedinCrossCheck {
  match_score: number;
  consistent: boolean;
  summary: string;
  mismatches: ConsistencyMismatch[];
}

interface CandidateDetail {
  candidate_ref: string;
  full_name: string;
  current_title: string | null;
  primary_domain: string | null;
  total_experience_years: number | null;
  location: string | null;
  email: string;
  phone: string;
  target_role: string | null;
  overall_score: number | null;
  resume_overall_score: number | null;
  l1_status: string | null;
  readiness_score: number | null;
  verification_status: string;
  github_url: string | null;
  linkedin_url: string | null;
  current_ctc: string | null;
  expected_ctc: string | null;
  notice_period: string | null;
  working_status: string | null;
  preferred_location: string | null;
  resume_analysis: ResumeAnalysis | null;
  linkedin_cross_check: LinkedinCrossCheck | null;
  top_skills: string[];
  skills: { name: string; proficiency: string; years: number | null; category: string }[];
  experience: { company: string; title: string; start_date: string | null; end_date: string | null; duration_months: number | null; is_current: boolean; domain: string | null; company_type: string | null }[];
  education: { institution: string; degree: string; field: string; graduation_year: number | null }[];
  interview: {
    interview_ref: string;
    overall_score: number | null;
    l1_status: string | null;
    recommendation: string | null;
    video_url: string | null;
    transcript: string | null;
    // The backend sends the full evaluation_data blob here, not just the sub-scores.
    // The per-category sub-scores live at `evaluation.evaluation` (nested).
    evaluation: {
      evaluation?: Record<string, { score: number; assessment: string }>;
      [k: string]: unknown;
    } | null;
    questions: { question: string; category: string; difficulty: string; answer_quality: string | null; score: number | null; answer_text: string | null }[];
  } | null;
  all_interviews: { interview_ref: string; overall_score: number | null; l1_status: string | null; created_at: string }[];
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

const VALUE_ADD_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  ACHIEVEMENT: Trophy,
  CERTIFICATION: Award,
  OPEN_SOURCE: Code2,
  LEADERSHIP: Users,
  PUBLICATION: BookOpen,
  AWARD: Award,
  SIDE_PROJECT: Sparkles,
};
const VALUE_ADD_TONE: Record<string, string> = {
  ACHIEVEMENT: "bg-amber-50 text-amber-700 border-amber-100",
  CERTIFICATION: "bg-sky-50 text-sky-700 border-sky-100",
  OPEN_SOURCE: "bg-slate-50 text-slate-700 border-slate-200",
  LEADERSHIP: "bg-violet-50 text-violet-700 border-violet-100",
  PUBLICATION: "bg-emerald-50 text-emerald-700 border-emerald-100",
  AWARD: "bg-yellow-50 text-yellow-700 border-yellow-100",
  SIDE_PROJECT: "bg-pink-50 text-pink-700 border-pink-100",
};

function scoreTone(score: number | null | undefined): string {
  if (score == null) return "text-slate-500 bg-slate-100";
  if (score >= 85) return "text-green-700 bg-green-100";
  if (score >= 70) return "text-emerald-700 bg-emerald-100";
  if (score >= 50) return "text-amber-700 bg-amber-100";
  return "text-red-600 bg-red-100";
}

function tenureLabel(months: number): string {
  if (!months) return "—";
  if (months < 12) return `${months}mo`;
  const yrs = Math.floor(months / 12);
  const rem = months % 12;
  return rem ? `${yrs}y ${rem}mo` : `${yrs}y`;
}

function formatDuration(months: number | null) {
  if (!months) return "";
  if (months < 12) return `${months}mo`;
  return `${Math.floor(months / 12)}y${months % 12 ? ` ${months % 12}mo` : ""}`;
}

export default function CandidateDetailPage() {
  const { ref } = useParams<{ ref: string }>();
  const router = useRouter();
  const [data, setData] = useState<CandidateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"overview" | "resume" | "linkedin" | "interview" | "questions">("overview");
  const [reinterviewLoading, setReinterviewLoading] = useState(false);
  const [reinterviewDone, setReinterviewDone] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    api.get(`hiring-manager/candidates/${ref}`).json<CandidateDetail>()
      .then(setData).finally(() => setLoading(false));
  }, [ref]);

  async function handleAllowReinterview() {
    if (!confirm(`Allow ${data?.full_name} to retake the interview?`)) return;
    setReinterviewLoading(true);
    try {
      await api.post(`hiring-manager/candidates/${ref}/allow-reinterview`).json();
      setReinterviewDone(true);
    } finally {
      setReinterviewLoading(false);
    }
  }

  async function handleDelete() {
    if (
      !confirm(
        `Permanently delete ${data?.full_name}?\n\nThis removes their entire record — profile, resume, ID documents, interviews and scores — from the database. This cannot be undone.`
      )
    )
      return;
    setDeleteLoading(true);
    try {
      await api.delete(`hiring-manager/candidates/${ref}`).json();
      router.push("/hiring-manager/candidates");
    } catch {
      setDeleteLoading(false);
      alert("Failed to delete candidate. Please try again.");
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="h-6 w-6 animate-spin text-green-600" />
    </div>
  );
  if (!data) return <p className="text-slate-500">Candidate not found.</p>;

  const passed = data.l1_status === "PASSED";

  return (
    <div className="space-y-6">
      <Link href="/hiring-manager/candidates" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors">
        <ArrowLeft className="h-4 w-4" /> Back to candidates
      </Link>

      {/* Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-green-100 text-green-700 text-2xl font-bold">
              {data.full_name.charAt(0)}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl font-bold text-slate-800">{data.full_name}</h1>
                {data.verification_status === "VERIFIED" && (
                  <span className="flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2.5 py-1 rounded-full font-semibold">
                    <CheckCircle2 className="h-3 w-3" /> Verified
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-500 mt-0.5">{data.current_title || data.primary_domain}</p>
              <div className="flex items-center gap-4 mt-2 text-xs text-slate-400 flex-wrap">
                {data.email && <span className="flex items-center gap-1"><Mail className="h-3 w-3" />{data.email}</span>}
                {data.phone && <span className="flex items-center gap-1"><Phone className="h-3 w-3" />{data.phone}</span>}
                {data.location && <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{data.location}</span>}
                {data.linkedin_url && (
                  <a href={data.linkedin_url} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sky-600 hover:text-sky-700">
                    <Linkedin className="h-3 w-3" /> LinkedIn
                  </a>
                )}
                {data.github_url && (
                  <a href={data.github_url} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-800">
                    <Github className="h-3 w-3" /> GitHub
                  </a>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end gap-3">
            <div className="flex items-stretch gap-2">
              {data.resume_overall_score !== null && data.resume_overall_score !== undefined && (
                <div className={`text-center rounded-2xl p-4 min-w-25 border ${scoreTone(data.resume_overall_score).replace("text-", "border-").replace("bg-", "bg-")}`}>
                  <FileText className="h-6 w-6 mx-auto mb-1 text-slate-600" />
                  <p className={`text-2xl font-bold ${scoreTone(data.resume_overall_score).split(" ")[0]}`}>{Math.round(data.resume_overall_score)}</p>
                  <p className="text-xs font-semibold text-slate-500">Resume</p>
                </div>
              )}
              {data.overall_score !== null && (
                <div className={`text-center rounded-2xl p-4 min-w-25 ${passed ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"}`}>
                  {passed ? <Trophy className="h-6 w-6 mx-auto text-green-600 mb-1" /> : <XCircle className="h-6 w-6 mx-auto text-red-500 mb-1" />}
                  <p className={`text-2xl font-bold ${passed ? "text-green-700" : "text-red-600"}`}>{data.overall_score}%</p>
                  <p className="text-xs font-semibold text-slate-500">L1 Score</p>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              {data.interview && (
                reinterviewDone ? (
                  <span className="flex items-center gap-1.5 text-xs text-green-600 font-semibold bg-green-50 border border-green-200 px-3 py-2 rounded-xl">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Re-interview enabled
                  </span>
                ) : (
                  <button onClick={handleAllowReinterview} disabled={reinterviewLoading}
                    className="flex items-center gap-2 text-xs font-semibold text-white bg-amber-500 hover:bg-amber-600 disabled:opacity-50 px-4 py-2 rounded-xl transition-colors">
                    {reinterviewLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                    Give Another Chance
                  </button>
                )
              )}
              <button onClick={handleDelete} disabled={deleteLoading}
                title="Permanently delete this candidate and all their data"
                className="flex items-center gap-2 text-xs font-semibold text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 disabled:opacity-50 px-4 py-2 rounded-xl transition-colors">
                {deleteLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
                Delete
              </button>
            </div>
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-3 gap-3 mt-6">
          <div className="text-center rounded-xl bg-slate-50 p-3">
            <p className="text-lg font-bold text-slate-800">{data.total_experience_years ? `${data.total_experience_years}y` : "—"}</p>
            <p className="text-xs text-slate-500">Experience</p>
          </div>
          <div className="text-center rounded-xl bg-slate-50 p-3">
            <p className="text-lg font-bold text-slate-800">{data.primary_domain || "—"}</p>
            <p className="text-xs text-slate-500">Domain</p>
          </div>
          <div className="text-center rounded-xl bg-slate-50 p-3">
            <p className="text-lg font-bold text-slate-800">{data.target_role || "—"}</p>
            <p className="text-xs text-slate-500">Target Role</p>
          </div>
        </div>
      </div>

      {/* Compensation row */}
      {(data.current_ctc || data.expected_ctc || data.notice_period || data.working_status || data.preferred_location) && (
        <div className="bg-white rounded-2xl border border-slate-200 p-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 text-sm">
          {data.current_ctc && (
            <div>
              <p className="flex items-center gap-1.5 text-xs text-slate-500"><IndianRupee className="h-3 w-3" /> Current CTC</p>
              <p className="font-semibold text-slate-800 mt-0.5">{data.current_ctc}</p>
            </div>
          )}
          {data.expected_ctc && (
            <div>
              <p className="flex items-center gap-1.5 text-xs text-slate-500"><IndianRupee className="h-3 w-3" /> Expected CTC</p>
              <p className="font-semibold text-slate-800 mt-0.5">{data.expected_ctc}</p>
            </div>
          )}
          {data.notice_period && (
            <div>
              <p className="flex items-center gap-1.5 text-xs text-slate-500"><Clock className="h-3 w-3" /> Notice Period</p>
              <p className="font-semibold text-slate-800 mt-0.5">{data.notice_period}</p>
            </div>
          )}
          {data.working_status && (
            <div>
              <p className="flex items-center gap-1.5 text-xs text-slate-500"><Activity className="h-3 w-3" /> Status</p>
              <p className="font-semibold text-slate-800 mt-0.5">{data.working_status}</p>
            </div>
          )}
          {data.preferred_location && (
            <div>
              <p className="flex items-center gap-1.5 text-xs text-slate-500"><MapPin className="h-3 w-3" /> Preferred Location</p>
              <p className="font-semibold text-slate-800 mt-0.5">{data.preferred_location}</p>
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit flex-wrap">
        {(["overview", "resume", "linkedin", "interview", "questions"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${tab === t ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}>
            {t}
          </button>
        ))}
      </div>

      {/* Overview tab */}
      {tab === "overview" && (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Skills */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
            <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2"><Star className="h-4 w-4 text-green-600" /> Skills</h2>
            <div className="flex flex-wrap gap-2">
              {data.skills.map((s, i) => (
                <span key={`${s.name}-${i}`} className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 whitespace-nowrap">
                  {s.name}
                </span>
              ))}
              {data.skills.length === 0 && <p className="text-xs text-slate-400">No skills recorded</p>}
            </div>
          </div>

          {/* Experience */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
            <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2"><Briefcase className="h-4 w-4 text-green-600" /> Experience</h2>
            <div className="space-y-3">
              {data.experience.map((e, i) => (
                <div key={i} className="flex gap-3">
                  <div className="mt-1.5 h-2 w-2 rounded-full bg-green-500 shrink-0" />
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-semibold text-slate-800">{e.title}</p>
                      {e.company_type && (
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${COMPANY_TYPE_TONE[e.company_type] ?? COMPANY_TYPE_TONE.OTHER}`}>
                          <Building2 className="h-2.5 w-2.5" />
                          {COMPANY_TYPE_LABEL[e.company_type] ?? e.company_type}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500">{e.company} · {formatDuration(e.duration_months)}</p>
                    <p className="text-xs text-slate-400">{e.start_date} — {e.is_current ? "Present" : e.end_date}</p>
                  </div>
                </div>
              ))}
              {data.experience.length === 0 && <p className="text-xs text-slate-400">No experience recorded</p>}
            </div>
          </div>

          {/* Education */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
            <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2"><GraduationCap className="h-4 w-4 text-green-600" /> Education</h2>
            <div className="space-y-3">
              {data.education.map((e, i) => (
                <div key={i}>
                  <p className="text-sm font-semibold text-slate-800">{e.degree} in {e.field}</p>
                  <p className="text-xs text-slate-500">{e.institution} {e.graduation_year ? `· ${e.graduation_year}` : ""}</p>
                </div>
              ))}
              {data.education.length === 0 && <p className="text-xs text-slate-400">No education recorded</p>}
            </div>
          </div>

          {/* Interview history */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
            <h2 className="text-sm font-semibold text-slate-700">Interview History</h2>
            <div className="space-y-2">
              {data.all_interviews.map((i) => (
                <div key={i.interview_ref} className="flex items-center justify-between text-sm">
                  <span className="text-slate-600 font-mono text-xs">{i.interview_ref}</span>
                  <div className="flex items-center gap-2">
                    {i.overall_score !== null && <span className="font-semibold text-slate-800">{i.overall_score}%</span>}
                    {i.l1_status && (
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${i.l1_status === "PASSED" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"}`}>
                        {i.l1_status}
                      </span>
                    )}
                    <span className="text-xs text-slate-400">{new Date(i.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
              {data.all_interviews.length === 0 && <p className="text-xs text-slate-400">No interviews yet</p>}
            </div>
          </div>
        </div>
      )}

      {/* Resume Analysis tab */}
      {tab === "resume" && (
        data.resume_analysis ? (
          <div className="space-y-6">
            {/* Summary card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                    <FileText className="h-4 w-4 text-green-600" /> Resume Analysis
                  </h2>
                  <p className="text-sm text-slate-600 mt-2">{data.resume_analysis.summary || "—"}</p>
                </div>
                <div className={`text-center rounded-2xl p-4 min-w-25 ${scoreTone(data.resume_analysis.overall_score)}`}>
                  <p className="text-3xl font-bold">{data.resume_analysis.overall_score}</p>
                  <p className="text-[10px] font-semibold uppercase tracking-wider opacity-75">Overall</p>
                </div>
              </div>

              {/* Sub-scores */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
                {[
                  { label: "Skills", value: data.resume_analysis.sub_scores.skills_score },
                  { label: "Experience", value: data.resume_analysis.sub_scores.experience_score },
                  { label: "Education", value: data.resume_analysis.sub_scores.education_score },
                  { label: "Value Add", value: data.resume_analysis.sub_scores.value_add_score },
                ].map((s) => (
                  <div key={s.label} className="rounded-xl border border-slate-200 p-3">
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-medium text-slate-600">{s.label}</span>
                      <span className={`font-bold ${scoreTone(s.value).split(" ")[0]}`}>{s.value}</span>
                    </div>
                    <Progress value={s.value} className="h-1.5" />
                  </div>
                ))}
              </div>
            </div>

            {/* Analytics grid */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
              <h2 className="text-sm font-semibold text-slate-700">Analytics</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-lg font-bold text-slate-800">{data.resume_analysis.analytics.job_count}</p>
                  <p className="text-xs text-slate-500">Job count</p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-lg font-bold text-slate-800">{tenureLabel(data.resume_analysis.analytics.avg_tenure_months)}</p>
                  <p className="text-xs text-slate-500">Avg tenure</p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-lg font-bold text-slate-800">{tenureLabel(data.resume_analysis.analytics.longest_tenure_months)}</p>
                  <p className="text-xs text-slate-500">Longest tenure</p>
                </div>
                <div className={`rounded-xl p-3 ${data.resume_analysis.analytics.employment_gap_months > 6 ? "bg-amber-50" : "bg-slate-50"}`}>
                  <p className={`text-lg font-bold ${data.resume_analysis.analytics.employment_gap_months > 6 ? "text-amber-700" : "text-slate-800"}`}>
                    {tenureLabel(data.resume_analysis.analytics.employment_gap_months)}
                  </p>
                  <p className="text-xs text-slate-500">Employment gaps</p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-lg font-bold text-slate-800">{data.resume_analysis.analytics.skill_count}</p>
                  <p className="text-xs text-slate-500">Skill count</p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-sm font-bold text-slate-800 capitalize">{data.resume_analysis.analytics.education_level.toLowerCase()}</p>
                  <p className="text-xs text-slate-500">Education level</p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3 col-span-2">
                  <p className="text-sm font-bold text-slate-800 truncate">{data.resume_analysis.analytics.top_domain || "—"}</p>
                  <p className="text-xs text-slate-500">Top domain</p>
                </div>
              </div>
            </div>

            {/* Company orientation breakdown */}
            {(() => {
              const a = data.resume_analysis!.analytics;
              const buckets = [
                { type: "PRODUCT", years: a.product_experience_years ?? 0 },
                { type: "SERVICE", years: a.service_experience_years ?? 0 },
                { type: "GCC", years: a.gcc_experience_years ?? 0 },
                { type: "STARTUP", years: a.startup_experience_years ?? 0 },
              ].filter((b) => b.years > 0);
              const totalShown = buckets.reduce((s, b) => s + b.years, 0);
              if (totalShown === 0) return null;
              return (
                <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
                  <div className="flex items-center justify-between gap-3 flex-wrap">
                    <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-emerald-600" /> Company Orientation
                    </h2>
                    {a.dominant_company_type && (
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border ${COMPANY_TYPE_TONE[a.dominant_company_type] ?? COMPANY_TYPE_TONE.OTHER}`}>
                        Dominant: {COMPANY_TYPE_LABEL[a.dominant_company_type] ?? a.dominant_company_type}
                      </span>
                    )}
                  </div>
                  {/* Stacked bar */}
                  <div className="flex h-3 rounded-full overflow-hidden bg-slate-100">
                    {buckets.map((b) => {
                      const pct = (b.years / totalShown) * 100;
                      const bg = b.type === "PRODUCT" ? "bg-emerald-500"
                        : b.type === "SERVICE" ? "bg-amber-500"
                        : b.type === "GCC" ? "bg-sky-500"
                        : "bg-violet-500";
                      return <div key={b.type} className={bg} style={{ width: `${pct}%` }} title={`${COMPANY_TYPE_LABEL[b.type]}: ${b.years}y`} />;
                    })}
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {buckets.map((b) => (
                      <div key={b.type} className={`rounded-xl border p-3 ${COMPANY_TYPE_TONE[b.type]}`}>
                        <p className="text-[10px] font-semibold uppercase tracking-wider opacity-75">{COMPANY_TYPE_LABEL[b.type]}</p>
                        <p className="text-lg font-bold">{b.years}y</p>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}

            {/* Value-add items */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
              <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-amber-500" /> Value Additions
              </h2>
              {data.resume_analysis.value_add_items.length === 0 ? (
                <p className="text-xs text-slate-400">No standout value-add items detected.</p>
              ) : (
                <div className="space-y-2">
                  {data.resume_analysis.value_add_items.map((v, i) => {
                    const Icon = VALUE_ADD_ICONS[v.category] ?? Sparkles;
                    const tone = VALUE_ADD_TONE[v.category] ?? "bg-slate-50 text-slate-700 border-slate-200";
                    return (
                      <div key={i} className={`flex items-start gap-3 rounded-xl border p-3 ${tone}`}>
                        <Icon className="h-4 w-4 mt-0.5 shrink-0" />
                        <div className="min-w-0">
                          <p className="text-[10px] font-semibold uppercase tracking-wider opacity-70">{v.category.replace(/_/g, " ")}</p>
                          <p className="text-sm leading-snug mt-0.5">{v.description}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
            <p className="text-slate-400 text-sm">No resume analysis available yet.</p>
          </div>
        )
      )}

      {/* LinkedIn cross-check tab */}
      {tab === "linkedin" && (
        data.linkedin_cross_check ? (
          (() => {
            const cc = data.linkedin_cross_check;
            const tone = cc.match_score >= 85 ? "green" : cc.match_score >= 60 ? "amber" : "red";
            const toneBg = tone === "green" ? "bg-green-50 border-green-200" : tone === "amber" ? "bg-amber-50 border-amber-200" : "bg-red-50 border-red-200";
            const toneText = tone === "green" ? "text-green-700" : tone === "amber" ? "text-amber-700" : "text-red-600";
            const Icon = tone === "green" ? ShieldCheck : ShieldAlert;
            return (
              <div className="space-y-4">
                <div className={`rounded-2xl border p-6 ${toneBg}`}>
                  <div className="flex items-center gap-5">
                    <Icon className={`h-12 w-12 shrink-0 ${toneText}`} />
                    <div className="flex-1">
                      <p className={`text-4xl font-bold ${toneText}`}>{cc.match_score}%</p>
                      <p className="text-sm font-medium text-slate-600 mt-1">{cc.summary}</p>
                    </div>
                    {data.linkedin_url && (
                      <a href={data.linkedin_url} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs font-medium text-sky-700 bg-white border border-sky-200 rounded-lg px-3 py-1.5 hover:bg-sky-50">
                        <Linkedin className="h-3.5 w-3.5" /> Open LinkedIn
                      </a>
                    )}
                  </div>
                </div>

                <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-3">
                  <h2 className="text-sm font-semibold text-slate-700">Mismatches</h2>
                  {cc.mismatches.length === 0 ? (
                    <p className="text-xs text-slate-400">No mismatches detected.</p>
                  ) : (
                    <ul className="space-y-2">
                      {cc.mismatches.map((m, i) => (
                        <li key={i} className="flex items-start gap-3 rounded-xl border border-slate-200 p-3">
                          <ShieldAlert className="h-4 w-4 mt-0.5 text-amber-500 shrink-0" />
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                              {m.type.replace(/_/g, " ")}{m.company ? ` · ${m.company}` : ""}
                            </p>
                            <p className="text-sm text-slate-700 mt-0.5">{m.details}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            );
          })()
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
            <p className="text-slate-400 text-sm">LinkedIn cross-check not available.</p>
          </div>
        )
      )}

      {/* Interview tab */}
      {tab === "interview" && data.interview && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">
          <div className={`rounded-xl p-5 flex items-center gap-5 ${passed ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"}`}>
            {passed ? <Trophy className="h-12 w-12 text-green-600 shrink-0" /> : <XCircle className="h-12 w-12 text-red-500 shrink-0" />}
            <div className="flex-1">
              <p className={`text-4xl font-bold ${passed ? "text-green-700" : "text-red-600"}`}>{data.interview.overall_score}%</p>
              <p className="text-sm font-medium text-slate-600 mt-1">{data.interview.recommendation?.replace(/_/g, " ") || data.interview.l1_status}</p>
            </div>
            {data.interview.video_url && (
              <a
                href={data.interview.video_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg px-3 py-2 hover:bg-slate-50 hover:border-slate-400 shrink-0"
              >
                <Video className="h-3.5 w-3.5 text-slate-500" />
                Recording
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>

          {data.interview.transcript && (
            <div className="rounded-xl border border-slate-200 p-4 space-y-2">
              <p className="text-xs font-semibold text-slate-600 flex items-center gap-1.5 uppercase tracking-wider">
                <MessageSquare className="h-3.5 w-3.5" /> Full Transcript
              </p>
              <pre className="whitespace-pre-wrap text-xs leading-relaxed text-slate-700 font-sans max-h-96 overflow-y-auto">{data.interview.transcript}</pre>
            </div>
          )}

          {(() => {
            // Sub-scores live one level deeper. Accept both shapes defensively.
            const raw = data.interview!.evaluation;
            const subScores = (raw?.evaluation ?? raw) as Record<string, { score?: number; assessment?: string }> | null | undefined;
            const entries = subScores
              ? Object.entries(subScores).filter(
                  ([, ev]) => ev && typeof ev === "object" && typeof (ev as { score?: unknown }).score === "number"
                )
              : [];
            if (entries.length === 0) return null;
            return (
              <div className="space-y-4">
                {entries.map(([cat, ev]) => {
                  const score = (ev as { score: number }).score;
                  const assessment = (ev as { assessment?: string }).assessment ?? "";
                  return (
                    <div key={cat}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="font-semibold capitalize text-slate-700">{cat.replace(/_/g, " ")}</span>
                        <span className={`font-bold ${score >= 60 ? "text-green-600" : "text-red-500"}`}>{score}%</span>
                      </div>
                      <Progress value={score} className="h-2" />
                      {assessment && <p className="text-xs text-slate-500 mt-1">{assessment}</p>}
                    </div>
                  );
                })}
              </div>
            );
          })()}
        </div>
      )}
      {tab === "interview" && !data.interview && (
        <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
          <p className="text-slate-400 text-sm">No interview completed yet.</p>
        </div>
      )}

      {/* Questions tab */}
      {tab === "questions" && data.interview && (
        <div className="space-y-3">
          {data.interview.questions.map((q, i) => {
            const qualityTone = q.answer_quality === "CORRECT"
              ? "bg-green-100 text-green-700"
              : q.answer_quality === "PARTIAL"
              ? "bg-amber-100 text-amber-700"
              : q.answer_quality === "INCORRECT"
              ? "bg-red-100 text-red-700"
              : "bg-slate-100 text-slate-600";
            return (
              <div key={i} className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <span className="text-xs font-semibold text-green-600 bg-green-50 px-2.5 py-1 rounded-full">{q.category}</span>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-[10px]">{q.difficulty}</Badge>
                    {q.answer_quality && (
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${qualityTone}`}>{q.answer_quality}</span>
                    )}
                    {q.score !== null && (
                      <span className={`text-xs font-bold ${q.score >= 60 ? "text-green-600" : "text-red-500"}`}>{q.score}%</span>
                    )}
                  </div>
                </div>
                <p className="text-sm font-medium text-slate-800">Q{i + 1}: {q.question}</p>
                {q.answer_text ? (
                  <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3 space-y-1">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1">
                      <MessageSquare className="h-3 w-3" /> Candidate&apos;s answer
                    </p>
                    <p className="text-xs leading-relaxed text-slate-700 whitespace-pre-wrap">{q.answer_text}</p>
                  </div>
                ) : (
                  q.answer_quality && (
                    <p className="text-xs text-slate-500">No transcript captured for this question.</p>
                  )
                )}
              </div>
            );
          })}
          {data.interview.questions.length === 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
              <p className="text-slate-400 text-sm">No questions recorded.</p>
            </div>
          )}
        </div>
      )}
      {tab === "questions" && !data.interview && (
        <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
          <p className="text-slate-400 text-sm">No interview completed yet.</p>
        </div>
      )}
    </div>
  );
}
