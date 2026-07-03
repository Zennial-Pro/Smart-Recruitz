"use client";

import { useOnboardingStore } from "@/stores/onboarding-store";
import { Check, User, FileText, ShieldCheck, Phone, Trophy } from "lucide-react";

const STEPS = [
  { id: "profile",   label: "Profile Setup",       sub: "Name, email & phone",   icon: User,        flows: ["name","email","phone","role","registering"] },
  { id: "resume",    label: "Resume",               sub: "Skills & experience",   icon: FileText,    flows: ["resume_upload","resume_parsing","resume_review","duplicate_check"] },
  { id: "identity",  label: "Identity Check",       sub: "Government ID",         icon: ShieldCheck, flows: ["id_select","id_upload","id_verifying","id_result"] },
  { id: "interview", label: "Phone Interview",      sub: "AI voice screening",    icon: Phone,       flows: ["interview_intro","recording","transcribing"] },
  { id: "results",   label: "Results",              sub: "Your evaluation score", icon: Trophy,      flows: ["scoring","results","done"] },
];

function getStepStatus(stepFlows: string[], currentFlow: string): "done" | "active" | "upcoming" {
  const allFlows = STEPS.flatMap((s) => s.flows);
  const currentIdx = allFlows.indexOf(currentFlow);
  const stepStartIdx = allFlows.indexOf(stepFlows[0]);
  const stepEndIdx = allFlows.indexOf(stepFlows[stepFlows.length - 1]);
  if (currentIdx > stepEndIdx) return "done";
  if (currentIdx >= stepStartIdx) return "active";
  return "upcoming";
}

export function OnboardingSteps() {
  const flowState = useOnboardingStore((s) => s.flowState);

  return (
    <div className="flex flex-col gap-0.5">
      {STEPS.map((step) => {
        const status = getStepStatus(step.flows, flowState);
        const Icon = step.icon;

        return (
          <div key={step.id} className="relative">

            <div className={`relative flex items-center gap-4 px-3 py-3.5 rounded-2xl transition-all duration-300 ${
              status === "active" ? "bg-violet-50 border border-violet-200/80" : ""
            }`}>
              {/* Pulse ring for active */}
              {status === "active" && (
                <div className="absolute left-2.75 top-3.5 h-10 w-10 rounded-full bg-violet-400/20 animate-ping" />
              )}

              {/* Icon */}
              <div className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl transition-all duration-300 ${
                status === "done"
                  ? "bg-linear-to-br from-violet-600 to-indigo-600 text-white shadow-md shadow-violet-200"
                  : status === "active"
                  ? "bg-white border-2 border-violet-500 text-violet-600 shadow-lg shadow-violet-100"
                  : "bg-violet-50 border border-violet-100 text-violet-300"
              }`}>
                {status === "done" ? <Check className="h-4 w-4" strokeWidth={3} /> : <Icon className="h-4 w-4" />}
              </div>

              {/* Text */}
              <div className={`transition-all duration-300 ${status === "upcoming" ? "opacity-40" : ""}`}>
                <p className={`text-sm font-semibold leading-tight ${
                  status === "active" ? "text-violet-700" :
                  status === "done"   ? "text-slate-700" : "text-slate-400"
                }`}>{step.label}</p>
                <p className={`text-xs mt-0.5 ${status === "active" ? "text-violet-500" : "text-slate-400"}`}>{step.sub}</p>
              </div>

              {/* Done badge */}
              {status === "done" && (
                <div className="ml-auto text-[10px] font-semibold text-violet-500 bg-violet-50 border border-violet-200 rounded-full px-2 py-0.5">done</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
