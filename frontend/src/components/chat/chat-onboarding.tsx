"use client";

import { useEffect, useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import { api } from "@/lib/api-client";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Upload, FileText, Loader2, CheckCircle2, AlertCircle,
  Send, Phone, PhoneCall, ShieldCheck, FileImage, Trophy, XCircle,
  UserRound, Target, ThumbsUp, PartyPopper, ClipboardList,
  Linkedin, Github, ShieldAlert,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type FlowState =
  | "first_name" | "last_name" | "email" | "phone" | "role"
  | "current_ctc" | "expected_ctc" | "notice_period" | "working_status" | "current_location" | "preferred_location"
  | "registering"
  | "resume_upload" | "resume_parsing" | "resume_review"
  | "github_url_collect" | "linkedin_url_collect" | "linkedin_crosscheck"
  | "duplicate_check"
  | "id_select" | "id_upload" | "id_verifying" | "id_result"
  | "interview_intro" | "recording" | "transcribing"
  | "scoring" | "results" | "done";

interface Msg {
  id: string;
  from: "bot" | "user";
  content: React.ReactNode;
  compact?: boolean;
}

interface ParsedResume {
  full_name: string; email: string; phone: string; current_title: string;
  primary_domain: string; confidence_score: number;
  github_url?: string; linkedin_url?: string;
  skills_normalized: { standard_name: string; proficiency: string }[];
  experience: { company: string; title: string; domain: string; start_date: string; end_date: string; duration_months: number; is_current: boolean }[];
  education: { institution: string; degree: string; field: string; graduation_year: number | null }[];
}
interface ConsistencyMismatch { type: string; company: string; details: string }
interface ConsistencyResult {
  match_score: number;
  consistent: boolean;
  summary: string;
  mismatches: ConsistencyMismatch[];
}
interface Question { q_id: string; category: string; question: string; targets_skill?: string; difficulty: string; time_estimate_seconds: number; }
interface ScoringResult {
  overall_score: number; l1_status: string; recommendation: string;
  evaluation: Record<string, { score: number; assessment: string }>;
  answer_validation: { question: string; answer?: string; answer_quality: string; score: number }[];
}

const uid = () => `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

const DOC_TYPE_LABELS: Record<string, string> = {
  AADHAAR_CARD: "Aadhaar Card",
  PAN_CARD: "PAN Card",
  PASSPORT: "Passport",
};

function formatDuration(months: number) {
  if (months < 12) return `${months} mo`;
  return `${Math.floor(months / 12)} yr${months % 12 > 0 ? ` ${months % 12} mo` : ""}`;
}

// Validate + normalize a profile URL. Accepts bare hosts ("github.com/x")
// and prepends https://. Returns null if it can't be coerced.
function normalizeProfileUrl(input: string, host: "github.com" | "linkedin.com"): string | null {
  const trimmed = input.trim().replace(/\s+/g, "");
  if (!trimmed) return null;
  const withScheme = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
  try {
    const u = new URL(withScheme);
    if (!u.hostname.toLowerCase().endsWith(host)) return null;
    // LinkedIn must point at /in/<slug>
    if (host === "linkedin.com" && !/\/in\/[^/]+/i.test(u.pathname)) return null;
    // GitHub must have a username path segment
    if (host === "github.com" && u.pathname.replace(/\/+$/, "") === "") return null;
    return u.toString().replace(/\/$/, "");
  } catch {
    return null;
  }
}
// Map raw verification flags to the highest-priority human-readable issue.
// Returns the first matching message in priority order, or a generic fallback.
function pickPrimaryIssue(flags: string[]): string | null {
  if (!flags || flags.length === 0) return null;
  const set = new Set(flags);

  // Priority order — most important reason first
  const order: Array<{ keys: string[]; message: string }> = [
    { keys: ["id_vs_entered_name_mismatch", "id_vs_resume_name_mismatch", "resume_vs_entered_name_mismatch", "name_mismatch"],
      message: "The name on your government ID doesn't match the name you provided." },
    { keys: ["image_edited", "font_inconsistency", "halo_around_text", "pixel_artifacts"],
      message: "The document appears to have been edited or tampered with." },
    { keys: ["id_number_unreadable"], message: "The ID number could not be read clearly. Please upload a sharper photo." },
    { keys: ["blurry_image"], message: "The image is too blurry. Please upload a clearer photo." },
    { keys: ["not_an_id_document"], message: "This doesn't look like a government-issued ID document." },
  ];

  for (const { keys, message } of order) {
    if (keys.some((k) => set.has(k))) return message;
  }
  // Fallback: humanize the first flag
  return flags[0].replace(/_/g, " ");
}

async function pollTask(taskId: string, interval = 3000, max = 60): Promise<{ result: unknown; error_message?: string; status: string }> {
  for (let i = 0; i < max; i++) {
    await sleep(interval);
    const t: { status: string; result: unknown; error_message?: string } = await api.get(`tasks/${taskId}`).json();
    if (t.status === "COMPLETED" || t.status === "FAILED") return t;
  }
  throw new Error("Task timed out");
}

interface InterviewStatusPayload {
  interview_ref: string;
  status: string;
  call_status?: string | null;
  overall_score?: number | null;
  l1_status?: string | null;
  recommendation?: string | null;
  evaluation?: Record<string, unknown> | null;
}

/**
 * Poll the voice-interview status until the call is SCORED (scoring arrives via
 * Zingaro's post-call webhook, so there is no client task id) or CALL_FAILED.
 * Calls onTick on each poll so the UI can reflect ringing/in-progress.
 */
async function pollInterviewStatus(
  interviewRef: string,
  onTick?: (s: InterviewStatusPayload) => void,
  interval = 4000,
  max = 150,
): Promise<InterviewStatusPayload> {
  for (let i = 0; i < max; i++) {
    await sleep(interval);
    const s: InterviewStatusPayload = await api.get(`voice-interview/${interviewRef}/status`).json();
    if (onTick) onTick(s);
    if (s.status === "SCORED" || s.status === "CALL_FAILED") return s;
  }
  throw new Error("Interview timed out");
}

// ─── Sub-components ────────────────────────────────────────────────────────────

function TypingDots() {
  return (
    <div className="flex items-center gap-1.5 px-1 py-1">
      {[0, 1, 2].map((i) => (
        <span key={i} className="h-2.5 w-2.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
      ))}
    </div>
  );
}

type CallPhase = "calling" | "in_progress" | "scoring";

/** Live status for the outbound voice interview: ringing → in progress → scoring. */
function CallStatusCard({ phase, phone }: { phase: CallPhase; phone?: string }) {
  const steps: { key: CallPhase; label: string }[] = [
    { key: "calling", label: "Calling" },
    { key: "in_progress", label: "In progress" },
    { key: "scoring", label: "Scoring" },
  ];
  const activeIdx = steps.findIndex((s) => s.key === phase);

  const headline =
    phase === "calling" ? "Calling you now" : phase === "in_progress" ? "Interview in progress" : "Call finished";
  const sub =
    phase === "calling" ? (
      <>
        Please <strong>pick up / answer the call</strong>
        {phone ? <> on <strong>{phone}</strong></> : null} from our AI interviewer, Charvi.
      </>
    ) : phase === "in_progress" ? (
      <>You&apos;re connected — answer each question clearly and keep this page open.</>
    ) : (
      <>Thanks! We&apos;re scoring your responses now — this only takes a few seconds.</>
    );

  return (
    <div className="w-full rounded-2xl border border-violet-100 bg-gradient-to-b from-violet-50/70 to-white p-5 space-y-4">
      <div className="flex items-center gap-4">
        <div className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-violet-100">
          {phase === "scoring" ? (
            <Loader2 className="h-6 w-6 animate-spin text-violet-600" />
          ) : (
            <>
              {phase === "calling" && <span className="absolute inset-0 rounded-2xl bg-violet-400/30 animate-ping" />}
              <PhoneCall className={`relative h-6 w-6 text-violet-600 ${phase === "calling" ? "animate-pulse" : ""}`} />
            </>
          )}
        </div>
        <div className="min-w-0">
          <p className="font-semibold text-slate-800">{headline}</p>
          <p className="text-sm text-slate-600">{sub}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {steps.map((s, i) => (
          <div key={s.key} className="flex flex-1 items-center gap-2">
            <span
              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                i < activeIdx
                  ? "bg-green-500 text-white"
                  : i === activeIdx
                  ? "bg-violet-600 text-white"
                  : "bg-slate-200 text-slate-500"
              }`}
            >
              {i < activeIdx ? "✓" : i + 1}
            </span>
            <span className={`text-xs ${i === activeIdx ? "font-semibold text-violet-700" : "text-slate-500"}`}>{s.label}</span>
            {i < steps.length - 1 && <span className={`h-px flex-1 ${i < activeIdx ? "bg-green-400" : "bg-slate-200"}`} />}
          </div>
        ))}
      </div>
    </div>
  );
}

function ResumeCard({ r }: { r: ParsedResume }) {
  const totalMonths = r.experience.reduce((s, e) => s + e.duration_months, 0);
  const exp = totalMonths < 12 ? `${totalMonths} months` : `${(totalMonths / 12).toFixed(1)} years`;
  return (
    <div className="rounded-2xl border bg-card p-4 space-y-4 text-sm w-full">
      <div className="flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-xl font-bold text-primary">
          {r.full_name?.charAt(0)}
        </div>
        <div>
          <p className="font-semibold text-base">{r.full_name}</p>
          <p className="text-muted-foreground">{r.current_title}</p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 text-center">
        {[{ l: "Experience", v: exp }, { l: "Domain", v: r.primary_domain }].map((s) => (
          <div key={s.l} className="rounded-lg bg-muted/50 p-2">
            <p className="font-semibold text-xs">{s.v}</p>
            <p className="text-[10px] text-muted-foreground">{s.l}</p>
          </div>
        ))}
      </div>
      {(r.github_url || r.linkedin_url) && (
        <div className="flex flex-wrap gap-2 text-xs">
          {r.linkedin_url && (
            <a href={r.linkedin_url} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-md bg-sky-50 border border-sky-100 px-2 py-1 text-sky-700 hover:bg-sky-100 truncate max-w-[48%]">
              <Linkedin className="h-3 w-3 shrink-0" />
              <span className="truncate">{r.linkedin_url.replace(/^https?:\/\//, "")}</span>
            </a>
          )}
          {r.github_url && (
            <a href={r.github_url} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-md bg-slate-50 border border-slate-200 px-2 py-1 text-slate-700 hover:bg-slate-100 truncate max-w-[48%]">
              <Github className="h-3 w-3 shrink-0" />
              <span className="truncate">{r.github_url.replace(/^https?:\/\//, "")}</span>
            </a>
          )}
        </div>
      )}
      {r.skills_normalized.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Skills</p>
          <div className="flex flex-wrap gap-1.5">
            {r.skills_normalized.slice(0, 8).map((s) => (
              <Badge key={s.standard_name} variant={s.proficiency === "EXPERT" || s.proficiency === "ADVANCED" ? "default" : "secondary"} className="text-xs">
                {s.standard_name}
              </Badge>
            ))}
            {r.skills_normalized.length > 8 && <Badge variant="outline" className="text-xs">+{r.skills_normalized.length - 8}</Badge>}
          </div>
        </div>
      )}
      {r.experience.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Experience</p>
          <div className="space-y-2">
            {r.experience.map((e, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className="mt-1.5 h-2 w-2 rounded-full bg-primary shrink-0" />
                <div>
                  <p className="font-medium leading-tight">{e.title} · {e.company}</p>
                  <p className="text-[11px] text-muted-foreground">
                    {e.start_date} — {e.is_current ? "Present" : e.end_date} ({formatDuration(e.duration_months)})
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ScoreCard({ d }: { d: ScoringResult }) {
  const passed = d.l1_status === "PASSED";
  return (
    <div className="rounded-2xl border bg-card p-4 space-y-4 w-full">
      <div className={`rounded-xl p-4 flex items-center gap-4 ${passed ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"}`}>
        {passed ? <Trophy className="h-10 w-10 text-green-600" /> : <XCircle className="h-10 w-10 text-red-500" />}
        <div>
          <p className={`text-3xl font-bold ${passed ? "text-green-700" : "text-red-600"}`}>{d.overall_score}%</p>
          <p className="text-sm font-medium">{d.recommendation.replace(/_/g, " ")}</p>
        </div>
      </div>
      <div className="space-y-3">
        {Object.entries(d.evaluation).map(([cat, ev]) => (
          <div key={cat}>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-medium capitalize">{cat.replace(/_/g, " ")}</span>
              <span className={ev.score >= 60 ? "text-green-600 font-bold" : "text-red-500 font-bold"}>{ev.score}%</span>
            </div>
            <Progress value={ev.score} className="h-1.5" />
            <p className="text-[11px] text-muted-foreground mt-0.5">{ev.assessment}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── File Upload Widget ────────────────────────────────────────────────────────

function ResumeUploadWidget({ onUpload }: { onUpload: (f: File) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (a) => a[0] && setFile(a[0]),
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"], "image/*": [".png", ".jpg", ".jpeg"] },
    maxSize: 10 * 1024 * 1024, maxFiles: 1,
  });
  return (
    <div className="space-y-3 w-full">
      <div {...getRootProps()} className={`cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-all ${isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}`}>
        <input {...getInputProps()} />
        <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
        <p className="text-sm font-medium">{isDragActive ? "Drop it here" : "Drag & drop or click to browse"}</p>
        <p className="text-xs text-muted-foreground mt-1">PDF, DOCX, PNG, JPG · Max 10MB</p>
      </div>
      {file && (
        <div className="flex items-center gap-3 rounded-xl border p-3">
          <FileText className="h-5 w-5 text-primary shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{file.name}</p>
            <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
          <Button size="sm" onClick={() => onUpload(file)}>Submit</Button>
        </div>
      )}
    </div>
  );
}

function IdUploadWidget({
  docType,
  onUpload,
  onSkip,
}: {
  docType: string;
  onUpload: (f: File, docType: string) => void;
  onSkip?: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (a) => a[0] && setFile(a[0]),
    accept: { "image/png": [".png"], "image/jpeg": [".jpg", ".jpeg"], "application/pdf": [".pdf"] },
    maxSize: 5 * 1024 * 1024, maxFiles: 1,
  });
  const label = DOC_TYPE_LABELS[docType] ?? docType;
  return (
    <div className="space-y-3 w-full">
      <div {...getRootProps()} className={`cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-all ${isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}`}>
        <input {...getInputProps()} />
        <ShieldCheck className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
        <p className="text-sm font-medium">Upload your <strong>{label}</strong></p>
        <p className="text-xs text-muted-foreground mt-1">PNG, JPG, PDF · Max 5MB</p>
      </div>
      {file && (
        <div className="flex items-center gap-3 rounded-xl border p-3">
          <FileImage className="h-5 w-5 text-primary shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{file.name}</p>
          </div>
          <Button size="sm" onClick={() => onUpload(file, docType)}>Verify</Button>
        </div>
      )}
      {onSkip && (
        <Button size="sm" variant="outline" className="w-full" onClick={onSkip}>
          Skip — I don&apos;t have a Passport
        </Button>
      )}
    </div>
  );
}

// ─── Main Chat Component ───────────────────────────────────────────────────────

export function ChatOnboarding() {
  const { setCandidateRef, updateCandidateData, candidateData, candidateRef, flowState, setFlowState } = useOnboardingStore();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [flow, setFlowLocal] = useState<FlowState>("first_name");
  const [input, setInput] = useState("");
  const [inputDisabled, setInputDisabled] = useState(false);
  const [widgetKey, setWidgetKey] = useState(0);
  const [currentIdDocType, setCurrentIdDocType] = useState<string>("AADHAAR_CARD");
  const bottomRef = useRef<HTMLDivElement>(null);

  function setFlow(f: FlowState) {
    setFlowLocal(f);
    setFlowState(f);
  }

  // local state refs for interview
  const candidateRefRef = useRef<string>("");
  const interviewRefRef = useRef<string>("");
  const greetedRef = useRef(false);

  function addMsg(from: "bot" | "user", content: React.ReactNode) {
    setMsgs((prev) => [...prev, { id: uid(), from, content }]);
  }

  async function botSay(content: React.ReactNode, delay = 600) {
    const typingId = uid();
    setMsgs((prev) => [...prev, { id: typingId, from: "bot", content: <TypingDots />, compact: true }]);
    await sleep(delay);
    setMsgs((prev) => prev.map((m) => m.id === typingId ? { ...m, content, compact: false } : m));
  }

  function showLoader(content: React.ReactNode): string {
    const id = uid();
    setMsgs((prev) => [...prev, { id, from: "bot", content }]);
    return id;
  }

  function replaceMsg(id: string, content: React.ReactNode) {
    setMsgs((prev) => prev.map((m) => m.id === id ? { ...m, content, compact: false } : m));
  }

  useEffect(() => {
    if (greetedRef.current) return;
    greetedRef.current = true;

    const saved = flowState as FlowState;
    const hasRef = !!candidateRef;
    const firstName = candidateData.first_name ?? candidateData.full_name?.split(" ")[0];

    // Restore pre-registration steps (name collected but no candidateRef yet)
    const preRegStates = [
      "last_name", "email", "phone", "role",
      "current_ctc", "expected_ctc", "notice_period", "working_status", "current_location", "preferred_location",
      "registering",
    ];
    if (!hasRef && candidateData.first_name && preRegStates.includes(saved)) {
      const resumePreReg = async () => {
        await botSay(
          <div className="space-y-1">
            <p className="font-semibold flex items-center gap-2"><UserRound className="h-4 w-4" /> Welcome back, {firstName}!</p>
            <p className="text-sm text-muted-foreground">Let&apos;s continue where you left off.</p>
          </div>, 500
        );
        if (!candidateData.last_name) {
          setFlowLocal("last_name");
          await botSay(<span>What&apos;s your <strong>last name</strong>?</span>);
        } else if (!candidateData.email) {
          setFlowLocal("email");
          await botSay(<span>What&apos;s your <strong>email address</strong>?</span>);
        } else if (!candidateData.phone) {
          setFlowLocal("phone");
          await botSay(<span>What&apos;s your <strong>phone number</strong>?</span>);
        } else if (saved === "role") {
          setFlowLocal("role");
          await botSay(<span>What role are you <strong>targeting</strong>? <em>(type &apos;skip&apos; to skip)</em></span>);
        } else if (saved === "current_ctc") {
          setFlowLocal("current_ctc");
          await botSay(<span>What&apos;s your <strong>current CTC</strong>? <em>(e.g. 12 LPA — type &apos;skip&apos; if not applicable)</em></span>);
        } else if (saved === "expected_ctc") {
          setFlowLocal("expected_ctc");
          await botSay(<span>And your <strong>expected CTC</strong>? <em>(e.g. 18 LPA)</em></span>);
        } else if (saved === "notice_period") {
          setFlowLocal("notice_period");
          await botSay(<span>What&apos;s your <strong>notice period</strong>? <em>(e.g. Immediate, 30 days, 60 days)</em></span>);
        } else if (saved === "working_status") {
          setFlowLocal("working_status");
          await botSay(<span>Are you <strong>currently working</strong>? <em>(Currently working / Serving notice / Not working)</em></span>);
        } else if (saved === "current_location") {
          setFlowLocal("current_location");
          await botSay(<span>Where are you <strong>currently located</strong>? <em>(e.g. Bangalore, India)</em></span>);
        } else if (saved === "preferred_location") {
          setFlowLocal("preferred_location");
          await botSay(<span>Which <strong>locations</strong> are you open to working in? <em>(e.g. Bangalore, Hyderabad, Remote)</em></span>);
        } else {
          // saved === "registering" with all required fields present
          setFlowLocal("registering");
          await register();
        }
      };
      resumePreReg();
      return;
    }

    // Restore session if candidate already registered
    if (hasRef && saved !== "first_name" && saved !== "last_name" && saved !== "email" && saved !== "phone" && saved !== "role" && saved !== "registering") {
      candidateRefRef.current = candidateRef!;

      const resumeToFlow = async () => {
        await botSay(
          <div className="space-y-1">
            <p className="font-semibold flex items-center gap-2"><UserRound className="h-4 w-4" /> Welcome back, {firstName}!</p>
            <p className="text-sm text-muted-foreground">Resuming where you left off...</p>
          </div>, 500
        );

        const atScoring = ["scoring", "results", "done"].includes(saved);
        const pastId = ["interview_intro","recording","transcribing","scoring","results","done"].includes(saved);
        const pastResume = pastId || ["id_select","id_upload","id_verifying","id_result","duplicate_check"].includes(saved);
        const atUrlCollection = ["github_url_collect", "linkedin_url_collect", "linkedin_crosscheck"].includes(saved);

        // Use completion flags as source of truth — never re-run a completed step
        // Fall back to flowState for sessions that predate the flags
        if (candidateData.scoringResult) {
          // Check if hiring manager granted a re-interview
          let reinterviewAllowed = false;
          try {
            const status = await api.get(`candidates/${candidateRefRef.current}/status`).json<{ reinterview_allowed: boolean }>();
            reinterviewAllowed = status.reinterview_allowed;
          } catch { /* ignore */ }

          if (reinterviewAllowed) {
            // Clear old results and let them re-interview
            updateCandidateData({ scoringResult: undefined, scoringTaskId: undefined });
            setFlowLocal("interview_intro");
            setFlow("interview_intro");
            await botSay(
              <div className="space-y-2">
                <p className="flex items-center gap-2 text-amber-600 font-medium"><Target className="h-4 w-4" /> A new interview opportunity has been granted!</p>
                <p className="text-sm">The hiring team has given you another chance. Ready to retake your <strong>phone interview</strong>?</p>
                <Button size="sm" className="mt-2" onClick={() => startInterview()}><Phone className="h-3.5 w-3.5 mr-1" /> Start Interview</Button>
              </div>
            );
            setInputDisabled(true);
          } else {
            // Result already cached — show instantly, no polling
            const score = candidateData.scoringResult as unknown as ScoringResult;
            setFlowLocal("results");
            setFlow("results");
            setInputDisabled(true);
            await botSay(
              <div className="space-y-3">
                <p className="font-semibold flex items-center gap-2">{score.l1_status === "PASSED" ? <><PartyPopper className="h-4 w-4 text-green-600" /> Congratulations! You passed!</> : <><ClipboardList className="h-4 w-4" /> Interview complete. Here are your results:</>}</p>
                <ScoreCard d={score} />
              </div>
            );
          }
        } else if (candidateData.scoringTaskId && atScoring) {
          // Scoring in-flight — poll once then cache
          setFlowLocal("scoring");
          setInputDisabled(true);
          await botSay(<span className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Preparing your evaluation...</span>, 400);
          try {
            const t = await pollTask(candidateData.scoringTaskId);
            const score = t.result as ScoringResult;
            updateCandidateData({ scoringResult: t.result as Record<string, unknown> });
            setFlow("results");
            await botSay(
              <div className="space-y-3">
                <p className="font-semibold flex items-center gap-2">{score.l1_status === "PASSED" ? <><PartyPopper className="h-4 w-4 text-green-600" /> Congratulations! You passed!</> : <><ClipboardList className="h-4 w-4" /> Interview complete. Here are your results:</>}</p>
                <ScoreCard d={score} />
              </div>
            );
          } catch {
            await botSay(<span className="text-destructive">Could not retrieve results. Please contact support.</span>);
          }
        } else if (candidateData.idVerified || pastId) {
          // ID verified — go straight to interview
          setFlowLocal("interview_intro");
          setFlow("interview_intro");
          await botSay(
            <div className="space-y-2">
              <p className="flex items-center gap-2 text-green-600 font-medium"><CheckCircle2 className="h-4 w-4" /> Identity verified!</p>
              <p className="text-sm">Ready to continue your <strong>phone interview</strong>?</p>
              <Button size="sm" className="mt-2" onClick={() => startInterview()}><Phone className="h-3.5 w-3.5 mr-1" /> Start Interview</Button>
            </div>
          );
          setInputDisabled(true);
        } else if (pastResume) {
          // Past the URL/cross-check stage — go to ID upload
          setFlowLocal("id_upload");
          setFlow("id_upload");
          setWidgetKey((k) => k + 1);
          await botSay(
            <div className="space-y-2">
              <p className="flex items-center gap-2 text-green-600 font-medium"><CheckCircle2 className="h-4 w-4" /> Resume verified!</p>
              <p className="text-sm">Now upload your <strong>government ID</strong> to continue.</p>
            </div>
          );
          setInputDisabled(true);
        } else if (candidateData.resumeConfirmed && !candidateData.github_url) {
          setFlowLocal("github_url_collect");
          setFlow("github_url_collect");
          await botSay(<span>I couldn&apos;t find a <strong>GitHub URL</strong> in your resume. Please paste it here. <em>(e.g. github.com/yourname)</em></span>);
        } else if (candidateData.resumeConfirmed && !candidateData.linkedin_url) {
          setFlowLocal("linkedin_url_collect");
          setFlow("linkedin_url_collect");
          await botSay(<span>I couldn&apos;t find a <strong>LinkedIn URL</strong> in your resume. Please paste it here. <em>(e.g. linkedin.com/in/yourname)</em></span>);
        } else if (candidateData.resumeConfirmed && !candidateData.linkedinCrossCheck) {
          // URLs collected but cross-check not done — re-trigger
          await runLinkedInCrossCheck();
        } else if (candidateData.resumeConfirmed || atUrlCollection) {
          // URLs collected and cross-check done — go to ID upload (resume at correct doc)
          const verified = candidateData.verifiedDocTypes ?? [];
          const nextDoc = !verified.includes("AADHAAR_CARD")
            ? "AADHAAR_CARD"
            : !verified.includes("PAN_CARD")
            ? "PAN_CARD"
            : "PASSPORT";
          setCurrentIdDocType(nextDoc);
          setFlowLocal("id_upload");
          setFlow("id_upload");
          setWidgetKey((k) => k + 1);
          const intro = verified.length === 0
            ? <p className="text-sm">Now upload your <strong>Aadhaar Card</strong> to start identity verification (step 1 of 2).</p>
            : verified.length === 1
            ? <p className="text-sm">Please continue with your <strong>{DOC_TYPE_LABELS[nextDoc]}</strong> (step 2 of 2).</p>
            : <p className="text-sm">Optionally upload a <strong>Passport</strong>, or skip to the interview.</p>;
          await botSay(
            <div className="space-y-2">
              <p className="flex items-center gap-2 text-green-600 font-medium"><CheckCircle2 className="h-4 w-4" /> Welcome back!</p>
              {intro}
            </div>
          );
          setInputDisabled(true);
        } else if (candidateData.parsedResume) {
          // Resume parsed but not yet confirmed — show card again
          const parsed = candidateData.parsedResume as unknown as ParsedResume;
          setFlowLocal("resume_review");
          setFlow("resume_review");
          setInputDisabled(true);
          await botSay(
            <div className="space-y-3">
              <p className="font-medium flex items-center gap-2"><ClipboardList className="h-4 w-4" /> Here&apos;s what I found in your resume</p>
              <ResumeCard r={parsed} />
              <div className="flex gap-2 mt-2">
                <Button size="sm" onClick={() => handleResumeConfirm()}><ThumbsUp className="h-3.5 w-3.5 mr-1" /> Looks good!</Button>
                <Button size="sm" variant="outline" onClick={() => handleResumeReupload()}>Re-upload</Button>
              </div>
            </div>
          );
        } else {
          // No resume yet — ask to upload
          setFlowLocal("resume_upload");
          setFlow("resume_upload");
          setWidgetKey((k) => k + 1);
          await botSay(<span>Please upload your <strong>resume</strong> to continue.</span>);
          setInputDisabled(true);
        }
      };

      resumeToFlow();
      return;
    }

    // Fresh start
    botSay(
      <div className="space-y-2">
        <p className="font-semibold text-base flex items-center gap-2"><UserRound className="h-4 w-4" /> Welcome to SmartRecruitz!</p>
        <p className="text-sm text-muted-foreground">I'll guide you through a one-time verification — takes about 10 minutes.</p>
        <p className="text-sm text-muted-foreground">This includes resume parsing, identity check, and a short phone interview.</p>
        <p className="text-sm font-medium mt-2">Let&apos;s start — what&apos;s your <strong>first name</strong>?</p>
      </div>, 800
    );
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setTimeout(() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }), 50);
  }, [msgs]);

  // ── Input submit ─────────────────────────────────────────────────────────────
  async function handleSend() {
    const val = input.trim();
    if (!val || inputDisabled) return;
    setInput("");
    addMsg("user", val);
    setInputDisabled(true);
    await handleFlow(val);
    setInputDisabled(false);
  }

  async function handleFlow(val: string) {
    if (flow === "first_name") {
      const cleaned = val.trim();
      if (!/^[A-Za-z][A-Za-z'\-]{0,49}$/.test(cleaned)) {
        await botSay(<span>That doesn&apos;t look like a valid first name. Please enter just your <strong>first name</strong>.</span>);
        setInputDisabled(false);
        return;
      }
      updateCandidateData({ first_name: cleaned });
      setFlow("last_name");
      await botSay(<span>Hi {cleaned}! And your <strong>last name</strong>?</span>);

    } else if (flow === "last_name") {
      const cleaned = val.trim();
      if (!/^[A-Za-z][A-Za-z'\- ]{0,49}$/.test(cleaned)) {
        await botSay(<span>That doesn&apos;t look like a valid last name. Please enter just your <strong>last name</strong>.</span>);
        setInputDisabled(false);
        return;
      }
      const fullName = `${candidateData.first_name ?? ""} ${cleaned}`.trim();

      // Validate the combined full name
      const checkingId = uid();
      setMsgs((prev) => [...prev, { id: checkingId, from: "bot", content: <TypingDots />, compact: true }]);
      try {
        const check = await api.post("candidates/validate-name", { json: { name: fullName } }).json<{ valid: boolean; reason: string }>();
        setMsgs((prev) => prev.filter((m) => m.id !== checkingId));
        if (!check.valid) {
          await botSay(<span>That doesn&apos;t look like a real name. Please enter your <strong>last name</strong>.</span>);
          setInputDisabled(false);
          return;
        }
      } catch {
        setMsgs((prev) => prev.filter((m) => m.id !== checkingId));
      }

      updateCandidateData({ last_name: cleaned, full_name: fullName });
      setFlow("email");
      await botSay(<span>Got it. What&apos;s your <strong>email address</strong>?</span>);

    } else if (flow === "email") {
      const cleanedEmail = val.trim();
      // RFC-ish strict pattern — matches what backend EmailStr accepts.
      // Local: letters, digits, ._%+- ; Domain: letters, digits, .- ; TLD: 2+ letters.
      const emailRe = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*\.[A-Za-z]{2,}$/;
      if (!emailRe.test(cleanedEmail)) {
        await botSay(<span>That doesn&apos;t look like a valid email. Please enter your <strong>email address</strong> (no spaces or special characters at the end).</span>);
        setInputDisabled(false);
        return;
      }
      updateCandidateData({ email: cleanedEmail });

      // Check if this email already has a profile — restore session from backend
      try {
        const lookup = await api.post("candidates/lookup", { json: { email: cleanedEmail } }).json<{
          found: boolean;
          candidate_ref?: string;
          full_name?: string;
          stage?: string;
          verified_doc_types?: string[];
          scoring_result?: Record<string, unknown> | null;
          reinterview_allowed?: boolean;
        }>();

        if (lookup.found && lookup.candidate_ref) {
          setCandidateRef(lookup.candidate_ref);
          candidateRefRef.current = lookup.candidate_ref;
          if (lookup.full_name) updateCandidateData({ full_name: lookup.full_name });

          if (lookup.scoring_result) {
            updateCandidateData({ scoringResult: lookup.scoring_result, idVerified: true, resumeConfirmed: true });
            const score = lookup.scoring_result as unknown as ScoringResult;

            if (lookup.reinterview_allowed) {
              updateCandidateData({ scoringResult: undefined });
              setFlow("interview_intro");
              setInputDisabled(true);
              await botSay(
                <div className="space-y-2">
                  <p className="flex items-center gap-2 text-amber-600 font-medium"><Target className="h-4 w-4" /> A new interview opportunity has been granted!</p>
                  <p className="text-sm">The hiring team has given you another chance. Ready to retake your <strong>phone interview</strong>?</p>
                  <Button size="sm" className="mt-2" onClick={() => startInterview()}><Phone className="h-3.5 w-3.5 mr-1" /> Start Interview</Button>
                </div>
              );
            } else {
              setFlow("results");
              setInputDisabled(true);
              await botSay(
                <div className="space-y-3">
                  <p className="font-semibold flex items-center gap-2">{score.l1_status === "PASSED" ? <><PartyPopper className="h-4 w-4 text-green-600" /> Congratulations! You passed!</> : <><ClipboardList className="h-4 w-4" /> Interview complete. Here are your results:</>}</p>
                  <ScoreCard d={score} />
                </div>
              );
            }
            return;
          }

          if (lookup.stage === "id_verified" || lookup.stage === "completed") {
            updateCandidateData({
              idVerified: true,
              resumeConfirmed: true,
              verifiedDocTypes: lookup.verified_doc_types ?? ["AADHAAR_CARD", "PAN_CARD"],
            });
            setFlow("interview_intro");
            setInputDisabled(true);
            await botSay(
              <div className="space-y-2">
                <p className="flex items-center gap-2 text-green-600 font-medium"><CheckCircle2 className="h-4 w-4" /> Identity verified!</p>
                <p className="text-sm">Ready to continue your <strong>phone interview</strong>?</p>
                <Button size="sm" className="mt-2" onClick={() => startInterview()}><Phone className="h-3.5 w-3.5 mr-1" /> Start Interview</Button>
              </div>
            );
            return;
          }

          if (lookup.stage === "id_partial") {
            // Some IDs verified but mandatory set incomplete — resume at next missing one
            const verified = lookup.verified_doc_types ?? [];
            updateCandidateData({ resumeConfirmed: true, verifiedDocTypes: verified });
            const nextDoc = !verified.includes("AADHAAR_CARD") ? "AADHAAR_CARD" : "PAN_CARD";
            setCurrentIdDocType(nextDoc);
            setFlow("id_upload");
            setInputDisabled(true);
            setWidgetKey((k) => k + 1);
            await botSay(
              <div className="space-y-2">
                <p className="flex items-center gap-2 text-green-600 font-medium"><CheckCircle2 className="h-4 w-4" /> Welcome back!</p>
                <p className="text-sm">Please upload your <strong>{DOC_TYPE_LABELS[nextDoc]}</strong> to finish identity verification.</p>
              </div>
            );
            return;
          }

          // Stage = registered — continue from resume upload
          updateCandidateData({ resumeConfirmed: false });
          setFlow("resume_upload");
          setInputDisabled(true);
          setWidgetKey((k) => k + 1);
          await botSay(<span>Welcome back! Please upload your <strong>resume</strong> to continue.</span>);
          return;
        }
      } catch { /* no existing profile — proceed normally */ }

      setFlow("phone");
      await botSay(<span>Got it! And your <strong>phone number</strong>?</span>);

    } else if (flow === "phone") {
      updateCandidateData({ phone: val });
      setFlow("role");
      await botSay(<span>What role are you <strong>targeting</strong>? <em>(type &apos;skip&apos; to skip)</em></span>);

    } else if (flow === "role") {
      const role = val.toLowerCase() === "skip" ? undefined : val;
      if (role) updateCandidateData({ target_role: role });
      setFlow("current_ctc");
      await botSay(<span>What&apos;s your <strong>current CTC</strong>? <em>(e.g. 12 LPA — type &apos;skip&apos; if not applicable)</em></span>);

    } else if (flow === "current_ctc") {
      const ctc = val.toLowerCase() === "skip" ? undefined : val.trim();
      if (ctc) updateCandidateData({ current_ctc: ctc });
      setFlow("expected_ctc");
      await botSay(<span>And your <strong>expected CTC</strong>? <em>(e.g. 18 LPA)</em></span>);

    } else if (flow === "expected_ctc") {
      const ctc = val.toLowerCase() === "skip" ? undefined : val.trim();
      if (ctc) updateCandidateData({ expected_ctc: ctc });
      setFlow("notice_period");
      await botSay(<span>What&apos;s your <strong>notice period</strong>? <em>(e.g. Immediate, 30 days, 60 days)</em></span>);

    } else if (flow === "notice_period") {
      const np = val.toLowerCase() === "skip" ? undefined : val.trim();
      if (np) updateCandidateData({ notice_period: np });
      setFlow("working_status");
      await botSay(<span>Are you <strong>currently working</strong>? <em>(Currently working / Serving notice / Not working)</em></span>);

    } else if (flow === "working_status") {
      const status = val.toLowerCase() === "skip" ? undefined : val.trim();
      if (status) updateCandidateData({ working_status: status });
      setFlow("current_location");
      await botSay(<span>Where are you <strong>currently located</strong>? <em>(e.g. Bangalore, India — or &apos;skip&apos;)</em></span>);

    } else if (flow === "current_location") {
      const cur = val.toLowerCase() === "skip" ? undefined : val.trim();
      if (cur) updateCandidateData({ location: cur });
      setFlow("preferred_location");
      await botSay(<span>Which <strong>locations</strong> are you open to working in? <em>(e.g. Bangalore, Hyderabad, Remote — comma-separated, or &apos;skip&apos;)</em></span>);

    } else if (flow === "preferred_location") {
      const loc = val.toLowerCase() === "skip" ? undefined : val.trim();
      if (loc) updateCandidateData({ preferred_location: loc });
      setFlow("registering");
      await register();

    } else if (flow === "github_url_collect") {
      const normalized = normalizeProfileUrl(val, "github.com");
      if (!normalized) {
        await botSay(<span>That doesn&apos;t look like a valid GitHub URL. Please paste it like <em>github.com/yourname</em>.</span>);
        setInputDisabled(false);
        return;
      }
      updateCandidateData({ github_url: normalized });
      // Decide what's next — LinkedIn missing or run cross-check
      if (!candidateData.linkedin_url) {
        setFlow("linkedin_url_collect");
        await botSay(<span>Thanks! Now your <strong>LinkedIn URL</strong>. <em>(e.g. linkedin.com/in/yourname)</em></span>);
      } else {
        await runLinkedInCrossCheck();
      }

    } else if (flow === "linkedin_url_collect") {
      const normalized = normalizeProfileUrl(val, "linkedin.com");
      if (!normalized) {
        await botSay(<span>That doesn&apos;t look like a valid LinkedIn URL. It should look like <em>linkedin.com/in/yourname</em>.</span>);
        setInputDisabled(false);
        return;
      }
      updateCandidateData({ linkedin_url: normalized });
      await runLinkedInCrossCheck();
    }
  }

  // ── Registration ─────────────────────────────────────────────────────────────
  async function register() {
    const loadingId = uid();
    setMsgs((prev) => [...prev, { id: loadingId, from: "bot", content: <span className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Creating your profile...</span> }]);
    try {
      const res = await api.post("candidates/register", {
        json: {
          full_name: candidateData.full_name,
          email: candidateData.email,
          phone: candidateData.phone,
          target_role: candidateData.target_role,
          current_ctc: candidateData.current_ctc,
          expected_ctc: candidateData.expected_ctc,
          notice_period: candidateData.notice_period,
          working_status: candidateData.working_status,
          location: candidateData.location,
          preferred_location: candidateData.preferred_location,
        },
      }).json<{ candidate_ref: string }>();
      setCandidateRef(res.candidate_ref);
      candidateRefRef.current = res.candidate_ref;
      setFlow("resume_upload");
      setMsgs((prev) => prev.map((m) => m.id === loadingId ? {
        ...m,
        content: (
          <div className="space-y-2">
            <p className="flex items-center gap-2 text-green-600 font-medium"><CheckCircle2 className="h-4 w-4" /> Profile created!</p>
            <p className="text-sm">Now upload your <strong>resume</strong> so I can extract your skills and experience.</p>
          </div>
        ),
      } : m));
      setInputDisabled(true);
      setWidgetKey((k) => k + 1);
    } catch {
      setMsgs((prev) => prev.map((m) => m.id === loadingId ? {
        ...m,
        content: <span className="text-destructive flex items-center gap-2"><AlertCircle className="h-4 w-4" /> Registration failed. Please try again.</span>,
      } : m));
      setFlow("first_name");
    }
  }

  // ── Resume Upload ─────────────────────────────────────────────────────────────
  async function handleResumeUpload(file: File) {
    setWidgetKey((k) => k + 1);
    addMsg("user", <span className="flex items-center gap-2"><FileText className="h-4 w-4" /> {file.name}</span>);
    setFlow("resume_parsing");
    const loaderId = showLoader(<span className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Analyzing your resume...</span>);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("candidate_ref", candidateRefRef.current);
      const { task_id } = await api.post("agent1/parse-resume", { body: fd }).json<{ task_id: string }>();
      const t = await pollTask(task_id);
      if (t.status === "FAILED") throw new Error(t.error_message);
      const parsed = t.result as ParsedResume;
      updateCandidateData({ parsedResume: t.result as Record<string, unknown> });
      setFlow("resume_review");
      replaceMsg(loaderId,
        <div className="space-y-3">
          <p className="font-medium flex items-center gap-2"><ClipboardList className="h-4 w-4" /> Here&apos;s what I found in your resume</p>
          <ResumeCard r={parsed} />
          <div className="flex gap-2 mt-2">
            <Button size="sm" onClick={() => handleResumeConfirm()}><ThumbsUp className="h-3.5 w-3.5 mr-1" /> Looks good!</Button>
            <Button size="sm" variant="outline" onClick={() => handleResumeReupload()}>Re-upload</Button>
          </div>
        </div>
      );
    } catch {
      setFlow("resume_upload");
      replaceMsg(loaderId, <span className="text-destructive flex items-center gap-2"><AlertCircle className="h-4 w-4" /> Resume parsing failed. Please try again.</span>);
      setWidgetKey((k) => k + 1);
    }
  }

  async function handleResumeConfirm() {
    addMsg("user", <span className="flex items-center gap-1.5"><ThumbsUp className="h-3.5 w-3.5" /> Looks good!</span>);
    updateCandidateData({ resumeConfirmed: true });

    // Stash any URLs the resume parser found into the store
    const parsed = candidateData.parsedResume as unknown as ParsedResume | undefined;
    const parsedGh = parsed?.github_url?.trim() || undefined;
    const parsedLi = parsed?.linkedin_url?.trim() || undefined;
    if (parsedGh && !candidateData.github_url) updateCandidateData({ github_url: parsedGh });
    if (parsedLi && !candidateData.linkedin_url) updateCandidateData({ linkedin_url: parsedLi });

    const haveGh = !!(candidateData.github_url || parsedGh);
    const haveLi = !!(candidateData.linkedin_url || parsedLi);

    if (!haveGh) {
      setFlow("github_url_collect");
      setInputDisabled(false);
      await botSay(<span>I couldn&apos;t find a <strong>GitHub URL</strong> in your resume. Please paste it here. <em>(e.g. github.com/yourname)</em></span>);
      return;
    }
    if (!haveLi) {
      setFlow("linkedin_url_collect");
      setInputDisabled(false);
      await botSay(<span>I couldn&apos;t find a <strong>LinkedIn URL</strong> in your resume. Please paste it here. <em>(e.g. linkedin.com/in/yourname)</em></span>);
      return;
    }

    await runLinkedInCrossCheck();
  }

  // ── LinkedIn x Resume cross-check ──────────────────────────────────────────
  async function runLinkedInCrossCheck() {
    setFlow("linkedin_crosscheck");
    setInputDisabled(true);
    const loaderId = showLoader(
      <span className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        Cross-checking your LinkedIn profile against your resume...
      </span>
    );
    try {
      // Read latest URLs directly from the store — `candidateData` in this closure
      // is the snapshot from the last render and may not reflect a just-set URL.
      const latest = useOnboardingStore.getState().candidateData;
      const { task_id } = await api.post("agent-consistency/cross-check", {
        json: {
          candidate_ref: candidateRefRef.current,
          github_url: latest.github_url,
          linkedin_url: latest.linkedin_url,
        },
      }).json<{ task_id: string }>();
      const t = await pollTask(task_id, 3000, 40);
      if (t.status === "FAILED") throw new Error(t.error_message);
      const res = t.result as ConsistencyResult;
      updateCandidateData({ linkedinCrossCheck: t.result as Record<string, unknown> });

      const score = res.match_score;
      const tone = score >= 85 ? "good" : score >= 60 ? "warn" : "bad";
      const Icon = tone === "good" ? CheckCircle2 : tone === "warn" ? ShieldAlert : AlertCircle;
      const toneColor = tone === "good" ? "text-green-600" : tone === "warn" ? "text-amber-600" : "text-red-600";
      const toneBg = tone === "good" ? "bg-green-50 border-green-100" : tone === "warn" ? "bg-amber-50 border-amber-100" : "bg-red-50 border-red-100";

      replaceMsg(loaderId,
        <div className="space-y-3">
          <p className={`font-semibold flex items-center gap-2 ${toneColor}`}>
            <Icon className="h-4 w-4" />
            LinkedIn match: {score}%
          </p>
          <div className={`rounded-xl border p-3 text-sm space-y-2 ${toneBg}`}>
            <p>{res.summary}</p>
            {res.mismatches.length > 0 && (
              <ul className="space-y-1 mt-1">
                {res.mismatches.slice(0, 4).map((m, i) => (
                  <li key={i} className="text-xs text-slate-700">
                    <span className="font-medium">{m.company || m.type.replace(/_/g, " ")}:</span> {m.details}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      );
      // Continue to duplicate check regardless of score; mismatches surface to hiring manager.
      await runDuplicateCheck();
    } catch {
      replaceMsg(loaderId,
        <div className="space-y-2">
          <p className="flex items-center gap-2 text-amber-600 text-sm"><ShieldAlert className="h-4 w-4" /> Couldn&apos;t complete LinkedIn cross-check.</p>
          <p className="text-xs text-muted-foreground">Don&apos;t worry — we&apos;ll continue. The hiring team will review manually.</p>
        </div>
      );
      await runDuplicateCheck();
    }
  }

  async function runDuplicateCheck() {
    setFlow("duplicate_check");
    const loaderId = showLoader(<span className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Running duplicate check...</span>);
    try {
      const { task_id } = await api.post(`agent2/check-duplicate?candidate_ref=${candidateRefRef.current}`).json<{ task_id: string }>();
      const t = await pollTask(task_id);
      const res = t.result as { result: string; reasoning: string };
      if (res.result === "DUPLICATE") {
        setFlow("done");
        replaceMsg(loaderId, <span className="text-destructive flex items-center gap-2"><AlertCircle className="h-4 w-4" /> A profile with your details already exists in our system. Please contact support.</span>);
        return;
      }
      setCurrentIdDocType("AADHAAR_CARD");
      setFlow("id_upload");
      replaceMsg(loaderId,
        <div className="space-y-2">
          <p className="flex items-center gap-2 text-green-600 font-medium"><CheckCircle2 className="h-4 w-4" /> Profile is unique!</p>
          <p className="text-sm">Now I need to verify your identity. Please upload your <strong>Aadhaar Card</strong> first (step 1 of 2).</p>
        </div>
      );
      setWidgetKey((k) => k + 1);
    } catch {
      replaceMsg(loaderId, <span className="text-destructive flex items-center gap-2"><AlertCircle className="h-4 w-4" /> Duplicate check failed. Please try again.</span>);
    }
  }

  async function handleResumeReupload() {
    addMsg("user", "Re-upload");
    setFlow("resume_upload");
    await botSay(<span>No problem! Upload a new resume below.</span>);
    setWidgetKey((k) => k + 1);
  }

  // ── ID Verification ───────────────────────────────────────────────────────────
  // Aadhaar + PAN are mandatory (in that order). Passport is optional at the end.
  async function handleIdUpload(file: File, docType: string) {
    setWidgetKey((k) => k + 1);
    addMsg("user", <span className="flex items-center gap-2"><FileImage className="h-4 w-4" /> {file.name} ({DOC_TYPE_LABELS[docType] ?? docType})</span>);
    setFlow("id_verifying");
    const loaderId = showLoader(<span className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Verifying your {DOC_TYPE_LABELS[docType] ?? "ID document"}...</span>);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("candidate_ref", candidateRefRef.current);
      fd.append("doc_type", docType);
      const { task_id } = await api.post("agent3/verify-identity", { body: fd }).json<{ task_id: string }>();
      const t = await pollTask(task_id);
      const res = t.result as {
        status: string;
        confidence_score: number;
        extracted_data: Record<string, string>;
        flags: string[];
        verified_doc_types?: string[];
        all_mandatory_verified?: boolean;
        mandatory_doc_types?: string[];
      };

      if (res.status !== "VERIFIED") {
        setCurrentIdDocType(docType);
        setFlow("id_upload");
        const primaryIssue = pickPrimaryIssue(res.flags ?? []);
        replaceMsg(loaderId,
          <div className="space-y-2">
            <p className="text-destructive flex items-center gap-2 font-medium"><AlertCircle className="h-4 w-4" /> Verification failed</p>
            {primaryIssue && <p className="text-sm text-muted-foreground">{primaryIssue}</p>}
            <p className="text-sm">Please upload a clear, unedited <strong>{DOC_TYPE_LABELS[docType] ?? "ID"}</strong> with your name and ID number visible.</p>
          </div>
        );
        setWidgetKey((k) => k + 1);
        return;
      }

      // Successful verification — persist progress + decide next step
      const verifiedDocTypes = res.verified_doc_types ?? [];
      const allMandatoryDone = !!res.all_mandatory_verified;
      updateCandidateData({
        verifiedDocTypes,
        idVerified: allMandatoryDone, // legacy flag — only true when both mandatory done
      });

      const extractedFields = Object.entries(res.extracted_data || {}).filter(([, v]) => v);
      const extractedBlock = extractedFields.length > 0 ? (
        <div className="rounded-xl border border-green-100 bg-green-50/50 p-3 space-y-1.5">
          {extractedFields.map(([key, val]) => (
            <div key={key} className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
              <span className="font-medium text-slate-700">{val}</span>
            </div>
          ))}
        </div>
      ) : null;

      // Decide what's next
      const justDid = docType;
      const needsPan = !verifiedDocTypes.includes("PAN_CARD");
      const passportAlreadyUploaded = verifiedDocTypes.includes("PASSPORT");

      if (justDid === "AADHAAR_CARD" && needsPan) {
        setCurrentIdDocType("PAN_CARD");
        setFlow("id_upload");
        replaceMsg(loaderId,
          <div className="space-y-3">
            <p className="flex items-center gap-2 text-green-600 font-medium"><CheckCircle2 className="h-4 w-4" /> Aadhaar verified!</p>
            {extractedBlock}
            <p className="text-sm">Now please upload your <strong>PAN Card</strong> (step 2 of 2).</p>
          </div>
        );
        setWidgetKey((k) => k + 1);
        return;
      }

      // PAN just verified OR Aadhaar uploaded out of order but PAN already done
      if (allMandatoryDone && !passportAlreadyUploaded && !candidateData.passportSkipped) {
        setCurrentIdDocType("PASSPORT");
        setFlow("id_upload");
        replaceMsg(loaderId,
          <div className="space-y-3">
            <p className="flex items-center gap-2 text-green-600 font-medium"><CheckCircle2 className="h-4 w-4" /> Identity verified!</p>
            {extractedBlock}
            <p className="text-sm">Optionally, you can also upload a <strong>Passport</strong> — useful for international placement.</p>
          </div>
        );
        setWidgetKey((k) => k + 1);
        return;
      }

      // All done — advance to interview
      setFlow("interview_intro");
      replaceMsg(loaderId,
        <div className="space-y-3">
          <p className="flex items-center gap-2 text-green-600 font-medium"><CheckCircle2 className="h-4 w-4" /> Identity verified!</p>
          {extractedBlock}
          <p className="text-sm">Almost there! Last step — a short <strong>phone interview</strong>.</p>
          <p className="text-sm text-muted-foreground">2 questions based on your resume. Each has a timer. Speak clearly — your answers will be transcribed.</p>
          <Button size="sm" className="mt-2" onClick={() => startInterview()}><Phone className="h-3.5 w-3.5 mr-1" /> Start Interview</Button>
        </div>
      );
    } catch {
      setCurrentIdDocType(docType);
      setFlow("id_upload");
      replaceMsg(loaderId, <span className="text-destructive flex items-center gap-2"><AlertCircle className="h-4 w-4" /> Verification failed. Please try again.</span>);
      setWidgetKey((k) => k + 1);
    }
  }

  function handlePassportSkip() {
    addMsg("user", <span className="flex items-center gap-1.5">Skip Passport</span>);
    updateCandidateData({ passportSkipped: true });
    setFlow("interview_intro");
    botSay(
      <div className="space-y-2">
        <p className="text-sm">No problem. Last step — a short <strong>phone interview</strong>.</p>
        <p className="text-sm text-muted-foreground">2 questions based on your resume. Each has a timer. Speak clearly — your answers will be transcribed.</p>
        <Button size="sm" className="mt-2" onClick={() => startInterview()}><Phone className="h-3.5 w-3.5 mr-1" /> Start Interview</Button>
      </div>
    );
  }

  // ── Interview ─────────────────────────────────────────────────────────────────
  async function startInterview() {
    addMsg("user", <span className="flex items-center gap-1.5"><Phone className="h-3.5 w-3.5" /> Start Interview</span>);
    setFlow("recording");
    const loaderId = showLoader(<span className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Preparing your interview...</span>);
    try {
      const { task_id } = await api.post(`agent4/generate-questions?candidate_ref=${candidateRefRef.current}`).json<{ task_id: string }>();
      const t = await pollTask(task_id, 3000, 60);
      const res = t.result as { interview_ref: string; questions: Question[] };
      interviewRefRef.current = res.interview_ref;
      updateCandidateData({ interviewRef: res.interview_ref });
      await runVoiceInterview(loaderId);
    } catch {
      replaceMsg(loaderId, <span className="text-destructive flex items-center gap-2"><AlertCircle className="h-4 w-4" /> Failed to generate questions. Please try again.</span>);
      setFlow("interview_intro");
    }
  }

  // Place the outbound voice call, then poll until the interview is scored.
  // Questions are injected into the agent at call time by our pre-call webhook —
  // nothing is recorded in the browser.
  async function runVoiceInterview(loaderId: string) {
    replaceMsg(loaderId, <CallStatusCard phase="calling" phone={candidateData.phone} />);
    try {
      await api.post("voice-interview/initiate", {
        json: { candidate_ref: candidateRefRef.current, interview_ref: interviewRefRef.current },
      }).json();
    } catch (e) {
      const status = (e as { response?: { status?: number } })?.response?.status;
      if (status !== 409) {
        replaceMsg(loaderId,
          <div className="space-y-2">
            <p className="text-destructive text-sm flex items-center gap-2"><AlertCircle className="h-4 w-4" /> We couldn&apos;t start the call.</p>
            <Button size="sm" variant="outline" onClick={() => startInterview()}><Phone className="h-3.5 w-3.5 mr-1" /> Try Again</Button>
          </div>
        );
        setFlow("interview_intro");
        return;
      }
      // 409 → a call is already in progress (e.g. the page was refreshed); resume polling.
    }
    try {
      const s = await pollInterviewStatus(interviewRefRef.current, (tick) => {
        const phase: CallPhase =
          tick.call_status === "COMPLETED"
            ? "scoring"
            : tick.call_status === "IN_PROGRESS" || tick.call_status === "RINGING"
            ? "in_progress"
            : "calling";
        replaceMsg(loaderId, <CallStatusCard phase={phase} phone={candidateData.phone} />);
      });
      if (s.status === "CALL_FAILED") {
        replaceMsg(loaderId,
          <div className="space-y-2">
            <p className="text-sm flex items-center gap-2"><AlertCircle className="h-4 w-4 text-destructive" /> We couldn&apos;t reach you on that call.</p>
            <Button size="sm" variant="outline" onClick={() => startInterview()}><Phone className="h-3.5 w-3.5 mr-1" /> Call me again</Button>
          </div>
        );
        setFlow("interview_intro");
        return;
      }
      const score = s.evaluation as unknown as ScoringResult;
      updateCandidateData({ scoringResult: s.evaluation as Record<string, unknown> });
      setFlow("results");
      replaceMsg(loaderId,
        <div className="space-y-3">
          <p className="font-semibold">{score.l1_status === "PASSED" ? "Congratulations! You passed!" : "Interview complete. Here are your results:"}</p>
          <ScoreCard d={score} />
          {score.l1_status === "PASSED" && (
            <p className="text-sm text-green-700 font-medium">You&apos;ve been added to the verified talent pool. Employers can now discover your profile!</p>
          )}
        </div>
      );
    } catch {
      replaceMsg(loaderId, <span className="text-destructive flex items-center gap-2"><AlertCircle className="h-4 w-4" /> The interview timed out. Please try again.</span>);
      setFlow("interview_intro");
    }
  }

  const showTextInput = ["first_name", "last_name", "email", "phone", "role", "current_ctc", "expected_ctc", "notice_period", "working_status", "current_location", "preferred_location", "github_url_collect", "linkedin_url_collect"].includes(flow);
  const showResumeWidget = flow === "resume_upload";
  const showIdWidget = flow === "id_upload";

  return (
    <div className="flex flex-col min-h-[calc(100vh-8rem)]">
      {/* Messages */}
      <div className="flex-1 space-y-8 pb-6">
        {msgs.map((m) => (
          <div key={m.id} className={`flex ${m.from === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-3 duration-300`}>
            {m.from === "bot" && (
              <div className="flex items-end gap-4 w-full">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-white text-sm font-bold shadow-lg shadow-violet-200/60" style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}>
                  SR
                </div>
                <div className={`${m.compact ? "w-fit" : "flex-1"} rounded-3xl rounded-bl-lg bg-white/90 backdrop-blur-sm border border-violet-100 shadow-lg shadow-violet-100/40 px-8 py-6 text-base leading-relaxed text-slate-700`}>
                  {m.content}
                </div>
              </div>
            )}
            {m.from === "user" && (
              <div className="rounded-3xl rounded-br-lg px-8 py-4 text-base leading-relaxed text-white max-w-[60%] shadow-lg shadow-violet-300/30" style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}>
                {m.content}
              </div>
            )}
          </div>
        ))}

        {/* Widgets */}
        {showResumeWidget && (
          <div className="flex items-end gap-4 w-full">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-white text-sm font-bold shadow-lg shadow-violet-200/60" style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}>SR</div>
            <div className="flex-1 rounded-3xl rounded-bl-lg bg-white/90 backdrop-blur-sm border border-violet-100 shadow-lg shadow-violet-100/40 px-8 py-6">
              <ResumeUploadWidget key={widgetKey} onUpload={handleResumeUpload} />
            </div>
          </div>
        )}
        {showIdWidget && (
          <div className="flex items-end gap-4 w-full">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-white text-sm font-bold shadow-lg shadow-violet-200/60" style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}>SR</div>
            <div className="flex-1 rounded-3xl rounded-bl-lg bg-white/90 backdrop-blur-sm border border-violet-100 shadow-lg shadow-violet-100/40 px-8 py-6">
              <IdUploadWidget
                key={widgetKey}
                docType={currentIdDocType}
                onUpload={handleIdUpload}
                onSkip={currentIdDocType === "PASSPORT" ? handlePassportSkip : undefined}
              />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      {showTextInput && (
        <div className="sticky bottom-0 pt-4 pb-2" style={{ background: "linear-gradient(to top, #ede9fe 60%, transparent)" }}>
          <div className="flex items-center gap-3 rounded-2xl bg-white/90 backdrop-blur-sm border border-violet-200/60 shadow-xl shadow-violet-100/30 px-5 py-3.5 focus-within:border-violet-400/60 focus-within:shadow-violet-200/50 transition-all duration-200">
            <input
              className="flex-1 bg-transparent text-[15px] outline-none placeholder:text-slate-400 disabled:opacity-50 text-slate-700"
              placeholder={
                flow === "first_name" ? "Enter your first name..." :
                flow === "last_name" ? "Enter your last name..." :
                flow === "email" ? "your@email.com" :
                flow === "phone" ? "+91 98765 43210" :
                flow === "role" ? "e.g. Senior Backend Engineer (or type 'skip')" :
                flow === "current_ctc" ? "e.g. 12 LPA (or 'skip')" :
                flow === "expected_ctc" ? "e.g. 18 LPA (or 'skip')" :
                flow === "notice_period" ? "e.g. Immediate, 30 days, 60 days" :
                flow === "working_status" ? "Currently working / Serving notice / Not working" :
                flow === "current_location" ? "e.g. Bangalore, India (or 'skip')" :
                flow === "preferred_location" ? "e.g. Bangalore, Hyderabad, Remote (or 'skip')" :
                flow === "github_url_collect" ? "github.com/yourname" :
                flow === "linkedin_url_collect" ? "linkedin.com/in/yourname" :
                ""
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={inputDisabled}
              autoFocus
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || inputDisabled}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white shadow-lg shadow-violet-300/40 disabled:opacity-30 hover:opacity-90 transition-all active:scale-95"
              style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
