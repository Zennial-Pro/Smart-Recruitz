"use client";

import { useOnboardingStore, type OnboardingStep } from "@/stores/onboarding-store";
import { Progress } from "@/components/ui/progress";

const STEPS: OnboardingStep[] = [
  "registration", "resume_upload", "resume_review",
  "duplicate_check", "id_verification", "interview_prep", "results",
];

const LABELS: Record<OnboardingStep, string> = {
  registration: "Registration",
  resume_upload: "Resume Upload",
  resume_review: "Profile Review",
  duplicate_check: "Duplicate Check",
  id_verification: "ID Verification",
  interview_prep: "Interview Prep",
  results: "Results",
  talent_pool: "Talent Pool",
};

export function MobileSteps() {
  const { currentStep } = useOnboardingStore();
  const currentIndex = STEPS.indexOf(currentStep);
  const progress = currentIndex >= 0 ? ((currentIndex + 1) / STEPS.length) * 100 : 0;

  return (
    <div className="mb-6 lg:hidden">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="font-medium">{LABELS[currentStep]}</span>
        <span className="text-muted-foreground">
          {currentIndex + 1} / {STEPS.length}
        </span>
      </div>
      <Progress value={progress} className="h-2" />
    </div>
  );
}
