"use client";

import { useOnboardingStore, type OnboardingStep } from "@/stores/onboarding-store";
import { Check } from "lucide-react";

const STEPS: { key: OnboardingStep; label: string }[] = [
  { key: "registration", label: "Register" },
  { key: "resume_upload", label: "Resume" },
  { key: "resume_review", label: "Review" },
  { key: "duplicate_check", label: "Verify" },
  { key: "id_verification", label: "ID Check" },
  { key: "interview_prep", label: "Interview" },
  { key: "results", label: "Results" },
];

export function ProgressTracker() {
  const { currentStep } = useOnboardingStore();
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <div className="flex items-center gap-1">
      {STEPS.map((step, i) => {
        const isComplete = i < currentIndex;
        const isCurrent = i === currentIndex;
        return (
          <div key={step.key} className="flex flex-1 flex-col items-center gap-1.5">
            <div
              className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold transition-colors ${
                isComplete
                  ? "bg-primary text-primary-foreground"
                  : isCurrent
                    ? "border-2 border-primary text-primary"
                    : "border border-border text-muted-foreground"
              }`}
            >
              {isComplete ? <Check className="h-4 w-4" /> : i + 1}
            </div>
            <span className={`text-xs leading-none ${isCurrent ? "font-semibold text-primary" : "text-muted-foreground"}`}>
              {step.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
