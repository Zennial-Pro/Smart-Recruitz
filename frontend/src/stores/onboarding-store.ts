"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type OnboardingStep =
  | "registration"
  | "resume_upload"
  | "resume_review"
  | "duplicate_check"
  | "id_verification"
  | "interview_prep"
  | "results"
  | "talent_pool";

interface CandidateData {
  first_name?: string;
  last_name?: string;
  full_name?: string;
  email?: string;
  phone?: string;
  target_role?: string;
  current_ctc?: string;
  expected_ctc?: string;
  notice_period?: string;
  working_status?: string;
  location?: string;
  preferred_location?: string;
  github_url?: string;
  linkedin_url?: string;
  parsedResume?: Record<string, unknown>;
  resumeConfirmed?: boolean;
  linkedinCrossCheck?: Record<string, unknown>;
  idVerified?: boolean; // legacy — true once all mandatory IDs are verified
  verifiedDocTypes?: string[]; // e.g. ["AADHAAR_CARD", "PAN_CARD"]
  passportSkipped?: boolean;
  interviewRef?: string;
  scoringTaskId?: string;
  scoringResult?: Record<string, unknown>;
}

interface OnboardingState {
  currentStep: OnboardingStep;
  candidateRef: string | null;
  candidateData: CandidateData;
  taskId: string | null;
  sessionKey: number;
  flowState: string;
  setStep: (step: OnboardingStep) => void;
  setCandidateRef: (ref: string) => void;
  setTaskId: (id: string | null) => void;
  updateCandidateData: (data: Partial<CandidateData>) => void;
  setFlowState: (flow: string) => void;
  reset: () => void;
}

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set) => ({
      currentStep: "registration",
      candidateRef: null,
      candidateData: {},
      taskId: null,
      sessionKey: 0,
      flowState: "first_name",
      setStep: (step) => set({ currentStep: step }),
      setCandidateRef: (ref) => set({ candidateRef: ref }),
      setTaskId: (id) => set({ taskId: id }),
      updateCandidateData: (data) =>
        set((state) => ({
          candidateData: { ...state.candidateData, ...data },
        })),
      setFlowState: (flow) => set({ flowState: flow }),
      reset: () =>
        set((state) => ({
          currentStep: "registration",
          candidateRef: null,
          candidateData: {},
          taskId: null,
          sessionKey: state.sessionKey + 1,
          flowState: "first_name",
        })),
    }),
    {
      name: "smartrecruitz-onboarding",
      storage: createJSONStorage(() => localStorage),
      skipHydration: true,
    }
  )
);
