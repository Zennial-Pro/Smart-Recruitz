"use client";

import { useOnboardingStore, type OnboardingStep } from "@/stores/onboarding-store";
import {
  Check,
  UserPlus,
  FileText,
  ClipboardCheck,
  Search,
  ShieldCheck,
  MessageSquareText,
  Trophy,
} from "lucide-react";

const STEPS: { key: OnboardingStep; label: string; description: string; icon: React.ElementType }[] = [
  { key: "registration", label: "Registration", description: "Basic information", icon: UserPlus },
  { key: "resume_upload", label: "Resume Upload", description: "Upload & AI parsing", icon: FileText },
  { key: "resume_review", label: "Profile Review", description: "Verify parsed data", icon: ClipboardCheck },
  { key: "duplicate_check", label: "Duplicate Check", description: "Profile uniqueness", icon: Search },
  { key: "id_verification", label: "ID Verification", description: "Document verification", icon: ShieldCheck },
  { key: "interview_prep", label: "Interview Prep", description: "AI-generated questions", icon: MessageSquareText },
  { key: "results", label: "Results", description: "Score & readiness", icon: Trophy },
];

export function StepSidebar() {
  const { currentStep } = useOnboardingStore();
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <aside className="hidden w-80 shrink-0 border-r bg-card lg:flex lg:flex-col overflow-hidden">
      <div className="px-6 pt-8 pb-4 shrink-0">
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Onboarding Steps
        </p>
      </div>
      <nav className="space-y-1 px-3 flex-1 overflow-y-auto">
        {STEPS.map((step, i) => {
          const isComplete = i < currentIndex;
          const isCurrent = i === currentIndex;
          const Icon = step.icon;

          return (
            <div
              key={step.key}
              className={`flex items-center gap-3 rounded-lg px-3 py-3 transition-colors ${
                isCurrent
                  ? "bg-primary/10 text-primary"
                  : isComplete
                    ? "text-foreground"
                    : "text-muted-foreground/50"
              }`}
            >
              <div
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition-colors ${
                  isComplete
                    ? "bg-primary text-primary-foreground"
                    : isCurrent
                      ? "border-2 border-primary bg-primary/10 text-primary"
                      : "border border-border bg-muted/50"
                }`}
              >
                {isComplete ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
              </div>
              <div className="min-w-0">
                <p
                  className={`text-sm leading-tight ${
                    isCurrent ? "font-semibold" : isComplete ? "font-medium" : ""
                  }`}
                >
                  {step.label}
                </p>
                <p
                  className={`text-xs truncate ${
                    isCurrent
                      ? "text-primary/70"
                      : isComplete
                        ? "text-muted-foreground"
                        : "text-muted-foreground/40"
                  }`}
                >
                  {step.description}
                </p>
              </div>
              {isComplete && (
                <span className="ml-auto text-xs font-medium text-green-600">Done</span>
              )}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
