"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { Search, X, Upload, Loader2, CheckCircle2, Star, Sparkles, Briefcase, Clock, FileText, ShieldAlert, AlertCircle } from "lucide-react";

interface CandidateCard {
  candidate_ref: string;
  full_name: string;
  current_title: string | null;
  primary_domain: string | null;
  total_experience_years: number | null;
  overall_score: number | null;
  l1_status: string | null;
  top_skills: string[];
  match_score?: number;
  matched_skills?: string[];
  matched_mandatory?: string[];
  matched_preferred?: string[];
  verification_status: string;
  location: string | null;
}

interface JDExtraction {
  role_title: string;
  role_level: string;
  domain: string;
  min_experience_years: number;
  mandatory_skills: string[];
  preferred_skills: string[];
  summary: string;
  extracted_text_preview?: string;
  extracted_text_length?: number;
}

type SkillBucket = "mandatory" | "preferred";

export default function SearchPage() {
  const [mandatoryInput, setMandatoryInput] = useState("");
  const [mandatorySkills, setMandatorySkills] = useState<string[]>([]);
  const [preferredInput, setPreferredInput] = useState("");
  const [preferredSkills, setPreferredSkills] = useState<string[]>([]);
  const [locationQuery, setLocationQuery] = useState("");
  const [jdText, setJdText] = useState("");
  const [jdFileName, setJdFileName] = useState<string | null>(null);
  const [jdExtraction, setJdExtraction] = useState<JDExtraction | null>(null);
  const [jdParsing, setJdParsing] = useState(false);
  const [jdError, setJdError] = useState<string | null>(null);
  const [results, setResults] = useState<CandidateCard[]>([]);
  const [matchedMandatory, setMatchedMandatory] = useState<string[]>([]);
  const [matchedPreferred, setMatchedPreferred] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  function addSkill(bucket: SkillBucket, s: string) {
    const trimmed = s.trim();
    if (!trimmed) return;
    const lower = trimmed.toLowerCase();
    const otherList = bucket === "mandatory" ? preferredSkills : mandatorySkills;
    const sameList = bucket === "mandatory" ? mandatorySkills : preferredSkills;
    if (sameList.some((x) => x.toLowerCase() === lower) || otherList.some((x) => x.toLowerCase() === lower)) {
      // Already present somewhere — silently ignore
      if (bucket === "mandatory") setMandatoryInput("");
      else setPreferredInput("");
      return;
    }
    if (bucket === "mandatory") {
      setMandatorySkills((p) => [...p, trimmed]);
      setMandatoryInput("");
    } else {
      setPreferredSkills((p) => [...p, trimmed]);
      setPreferredInput("");
    }
  }

  async function handleSearch() {
    if (
      mandatorySkills.length === 0 &&
      preferredSkills.length === 0 &&
      !jdText.trim() &&
      !locationQuery.trim()
    )
      return;
    setLoading(true);
    setSearched(false);
    try {
      const res = await api.post("hiring-manager/search", {
        json: {
          mandatory_skills: mandatorySkills,
          preferred_skills: preferredSkills,
          jd_text: jdText,
          location: locationQuery.trim(),
        },
      }).json<{
        mandatory_matched: string[];
        preferred_matched: string[];
        candidates: CandidateCard[];
      }>();
      setResults(res.candidates);
      setMatchedMandatory(res.mandatory_matched);
      setMatchedPreferred(res.preferred_matched);
      setSearched(true);
    } finally {
      setLoading(false);
    }
  }

  function mergeUnique(existing: string[], incoming: string[]): string[] {
    const seen = new Set(existing.map((s) => s.toLowerCase()));
    const merged = [...existing];
    for (const s of incoming) {
      const t = s.trim();
      if (t && !seen.has(t.toLowerCase())) {
        merged.push(t);
        seen.add(t.toLowerCase());
      }
    }
    return merged;
  }

  function applyExtraction(extraction: JDExtraction) {
    setJdExtraction(extraction);
    // De-conflict: mandatory wins over preferred.
    const mandLower = new Set(extraction.mandatory_skills.map((s) => s.toLowerCase()));
    const prefClean = extraction.preferred_skills.filter((s) => !mandLower.has(s.toLowerCase()));
    setMandatorySkills((prev) => mergeUnique(prev, extraction.mandatory_skills));
    setPreferredSkills((prev) => mergeUnique(prev, prefClean));
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setJdFileName(file.name);
    setJdError(null);
    setJdParsing(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await api.post("hiring-manager/extract-jd", { body: fd, timeout: 60000 }).json<JDExtraction>();
      if (res.extracted_text_preview) setJdText(res.extracted_text_preview);
      applyExtraction(res);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to parse JD";
      setJdError(message);
    } finally {
      setJdParsing(false);
    }
    // Allow re-uploading the same filename
    e.target.value = "";
  }

  async function handleParsePastedJd() {
    if (!jdText.trim()) return;
    setJdError(null);
    setJdParsing(true);
    try {
      const fd = new FormData();
      fd.append("jd_text", jdText);
      const res = await api.post("hiring-manager/extract-jd", { body: fd, timeout: 60000 }).json<JDExtraction>();
      applyExtraction(res);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to parse JD";
      setJdError(message);
    } finally {
      setJdParsing(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Search Candidates</h1>
        <p className="text-sm text-slate-500 mt-1">Upload a JD or enter skills to find matching candidates</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Search panel */}
        <div className="space-y-4">
          {/* JD upload */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
            <div>
              <p className="text-sm font-semibold text-slate-700">Upload Job Description</p>
              <p className="text-[11px] text-slate-500 mt-0.5">PDF, DOCX, or TXT. Skills auto-fill into both buckets below.</p>
            </div>
            <label className={`flex flex-col items-center justify-center gap-2 border-2 border-dashed rounded-xl p-6 cursor-pointer transition-all ${jdParsing ? "border-amber-300 bg-amber-50 cursor-wait" : "border-slate-200 hover:border-green-400 hover:bg-green-50"}`}>
              {jdParsing ? <Loader2 className="h-6 w-6 text-amber-500 animate-spin" /> : <Upload className="h-6 w-6 text-slate-400" />}
              <p className="text-xs text-slate-500 text-center">{jdParsing ? "Parsing JD..." : "Drop PDF/DOCX/TXT or click to browse"}</p>
              <input
                type="file"
                accept=".pdf,.txt,.docx,.doc"
                className="hidden"
                disabled={jdParsing}
                onChange={handleFileUpload}
              />
            </label>

            {/* Or paste */}
            <details className="text-xs text-slate-500">
              <summary className="cursor-pointer hover:text-slate-700">Or paste JD text directly</summary>
              <div className="mt-2 space-y-2">
                <textarea
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none focus:border-green-400 transition-colors min-h-25"
                  placeholder="Paste the job description here..."
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  disabled={jdParsing}
                />
                <button
                  onClick={handleParsePastedJd}
                  disabled={jdParsing || !jdText.trim()}
                  className="text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40 text-slate-700"
                >
                  {jdParsing ? "Parsing..." : "Extract skills"}
                </button>
              </div>
            </details>

            {jdFileName && !jdParsing && !jdError && (
              <div className="flex items-center gap-2 text-xs text-green-600 font-medium">
                <CheckCircle2 className="h-3.5 w-3.5" /> {jdFileName}
              </div>
            )}
            {jdError && (
              <div className="flex items-center gap-2 text-xs text-red-600 font-medium">
                <AlertCircle className="h-3.5 w-3.5" /> {jdError}
              </div>
            )}

            {/* Extracted metadata card */}
            {jdExtraction && !jdParsing && (
              <div className="rounded-xl border border-green-100 bg-green-50/40 p-3 space-y-2 text-xs">
                <p className="font-semibold text-slate-700 flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5 text-green-600" /> Parsed JD
                </p>
                {jdExtraction.summary && <p className="text-slate-600 leading-snug">{jdExtraction.summary}</p>}
                <div className="grid grid-cols-2 gap-2 pt-1">
                  {jdExtraction.role_title && (
                    <div className="flex items-center gap-1.5 text-slate-700">
                      <Briefcase className="h-3 w-3 text-slate-400 shrink-0" />
                      <span className="truncate"><b className="font-semibold">Role:</b> {jdExtraction.role_title}</span>
                    </div>
                  )}
                  {jdExtraction.role_level && (
                    <div className="flex items-center gap-1.5 text-slate-700">
                      <Star className="h-3 w-3 text-slate-400 shrink-0" />
                      <span className="truncate"><b className="font-semibold">Level:</b> {jdExtraction.role_level}</span>
                    </div>
                  )}
                  {jdExtraction.domain && (
                    <div className="flex items-center gap-1.5 text-slate-700">
                      <Sparkles className="h-3 w-3 text-slate-400 shrink-0" />
                      <span className="truncate"><b className="font-semibold">Domain:</b> {jdExtraction.domain}</span>
                    </div>
                  )}
                  {jdExtraction.min_experience_years > 0 && (
                    <div className="flex items-center gap-1.5 text-slate-700">
                      <Clock className="h-3 w-3 text-slate-400 shrink-0" />
                      <span className="truncate"><b className="font-semibold">Min exp:</b> {jdExtraction.min_experience_years}y</span>
                    </div>
                  )}
                </div>
                <p className="text-[10px] text-slate-500 pt-1">
                  Auto-filled {jdExtraction.mandatory_skills.length} mandatory + {jdExtraction.preferred_skills.length} preferred skills below. Edit before searching.
                </p>
              </div>
            )}
          </div>

          {/* Mandatory skills (strict filter) */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
            <div>
              <p className="text-sm font-semibold text-slate-700 flex items-center gap-1.5">
                <ShieldAlert className="h-3.5 w-3.5 text-red-500" /> Mandatory Skills
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">Hard filter — candidates without ALL of these are excluded.</p>
            </div>
            <div className="flex gap-2">
              <input
                className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-red-400 transition-colors"
                placeholder="Must-have skill + Enter"
                value={mandatoryInput}
                onChange={(e) => setMandatoryInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addSkill("mandatory", mandatoryInput)}
              />
              <button onClick={() => addSkill("mandatory", mandatoryInput)}
                className="px-3 py-2 rounded-lg bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition-colors">
                Add
              </button>
            </div>
            {mandatorySkills.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {mandatorySkills.map((s) => (
                  <span key={s} className="flex items-center gap-1 bg-red-100 text-red-700 text-xs font-medium px-2.5 py-1 rounded-full">
                    {s}
                    <button onClick={() => setMandatorySkills((p) => p.filter((x) => x !== s))}>
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Preferred skills */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
            <div>
              <p className="text-sm font-semibold text-slate-700 flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-sky-500" /> Preferred Skills
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">Nice-to-have. Boosts the match score but doesn&apos;t filter.</p>
            </div>
            <div className="flex gap-2">
              <input
                className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-400 transition-colors"
                placeholder="Bonus skill + Enter"
                value={preferredInput}
                onChange={(e) => setPreferredInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addSkill("preferred", preferredInput)}
              />
              <button onClick={() => addSkill("preferred", preferredInput)}
                className="px-3 py-2 rounded-lg bg-sky-500 text-white text-sm font-medium hover:bg-sky-600 transition-colors">
                Add
              </button>
            </div>
            {preferredSkills.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {preferredSkills.map((s) => (
                  <span key={s} className="flex items-center gap-1 bg-sky-100 text-sky-700 text-xs font-medium px-2.5 py-1 rounded-full">
                    {s}
                    <button onClick={() => setPreferredSkills((p) => p.filter((x) => x !== s))}>
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Location filter */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
            <div>
              <p className="text-sm font-semibold text-slate-700">Location</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Filters by the candidate&apos;s current OR preferred location.</p>
            </div>
            <input
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-green-400 transition-colors"
              placeholder="e.g. Bangalore, Remote"
              value={locationQuery}
              onChange={(e) => setLocationQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>

          <button
            onClick={handleSearch}
            disabled={loading || (mandatorySkills.length === 0 && preferredSkills.length === 0 && !jdText.trim() && !locationQuery.trim())}
            className="w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-40 text-white rounded-xl py-3 text-sm font-semibold transition-colors"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            {loading ? "Searching..." : "Search Candidates"}
          </button>
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-4">
          {(matchedMandatory.length > 0 || matchedPreferred.length > 0) && (
            <div className="space-y-1.5">
              {matchedMandatory.length > 0 && (
                <div className="flex flex-wrap gap-1.5 items-center">
                  <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                    <ShieldAlert className="h-3 w-3 text-red-500" /> Mandatory:
                  </span>
                  {matchedMandatory.map((s) => (
                    <span key={s} className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">{s}</span>
                  ))}
                </div>
              )}
              {matchedPreferred.length > 0 && (
                <div className="flex flex-wrap gap-1.5 items-center">
                  <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                    <Sparkles className="h-3 w-3 text-sky-500" /> Preferred:
                  </span>
                  {matchedPreferred.map((s) => (
                    <span key={s} className="text-xs bg-sky-100 text-sky-700 px-2 py-0.5 rounded-full font-medium">{s}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {searched && results.length === 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
              <p className="text-slate-500 text-sm">No matching candidates found.</p>
            </div>
          )}

          {results.map((c) => (
            <CandidateCardUI key={c.candidate_ref} c={c} />
          ))}
        </div>
      </div>
    </div>
  );
}

function CandidateCardUI({ c }: { c: CandidateCard }) {
  const passed = c.l1_status === "PASSED";
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-green-100 text-green-700 text-base font-bold">
            {c.full_name.charAt(0)}
          </div>
          <div>
            <p className="font-semibold text-slate-800">{c.full_name}</p>
            <p className="text-xs text-slate-500">{c.current_title || c.primary_domain || "—"}</p>
          </div>
        </div>
        {c.match_score !== undefined && (
          <span className={`text-sm font-bold px-3 py-1 rounded-full ${c.match_score === 100 ? "bg-green-600 text-white" : "bg-green-100 text-green-700"}`}>
            {c.match_score}% Match
          </span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3 text-center text-xs">
        <div className="rounded-lg bg-slate-50 p-2">
          <p className="font-semibold text-slate-800">{c.total_experience_years ? `${c.total_experience_years}y` : "—"}</p>
          <p className="text-slate-500">Experience</p>
        </div>
        <div className="rounded-lg bg-slate-50 p-2">
          <p className="font-semibold text-slate-800">{c.location || "—"}</p>
          <p className="text-slate-500">Location</p>
        </div>
        <div className={`rounded-lg p-2 ${c.overall_score !== null ? (passed ? "bg-green-50" : "bg-red-50") : "bg-slate-50"}`}>
          <p className={`font-semibold ${c.overall_score !== null ? (passed ? "text-green-700" : "text-red-600") : "text-slate-800"}`}>
            {c.overall_score !== null ? `${c.overall_score}%` : "—"}
          </p>
          <p className="text-slate-500">L1 Score</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {c.top_skills.map((s) => {
          const lower = s.toLowerCase();
          const isMand = c.matched_mandatory?.some((m) => m.toLowerCase() === lower || lower.includes(m.toLowerCase()));
          const isPref = c.matched_preferred?.some((m) => m.toLowerCase() === lower || lower.includes(m.toLowerCase()));
          const tone = isMand
            ? "bg-red-500 text-white"
            : isPref
            ? "bg-sky-500 text-white"
            : "bg-slate-100 text-slate-600";
          return <span key={s} className={`text-xs px-2 py-0.5 rounded-full font-medium ${tone}`}>{s}</span>;
        })}
      </div>

      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center gap-2">
          {c.verification_status === "VERIFIED" && (
            <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
              <CheckCircle2 className="h-3.5 w-3.5" /> Verified
            </span>
          )}
          {c.l1_status && (
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${passed ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"}`}>
              L1 {c.l1_status}
            </span>
          )}
        </div>
        <Link href={`/hiring-manager/candidates/${c.candidate_ref}`}
          className="text-xs font-semibold text-green-600 hover:text-green-700 flex items-center gap-1">
          View Profile <Star className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
