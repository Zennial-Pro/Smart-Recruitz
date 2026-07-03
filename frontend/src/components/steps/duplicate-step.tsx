"use client";

import { useEffect, useState } from "react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { api } from "@/lib/api-client";
import { useTaskPolling } from "@/hooks/use-task-polling";
import type { TaskCreatedResponse } from "@/types";
import { CheckCircle2, Database, Brain, ArrowRight, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { StepHeader } from "@/components/wizard/step-header";

type Phase = "db_scan" | "ai_compare" | "complete" | "duplicate" | "error";

export function DuplicateStep() {
  const { candidateRef, setStep } = useOnboardingStore();
  const [phase, setPhase] = useState<Phase>("db_scan");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { task, isCompleted, isFailed } = useTaskPolling({ taskId });

  // Trigger agent2 on mount
  useEffect(() => {
    if (!candidateRef) return;

    api
      .post("agent2/check-duplicate", { searchParams: { candidate_ref: candidateRef } })
      .json<TaskCreatedResponse>()
      .then((res) => {
        setTaskId(res.task_id);
        setPhase("ai_compare");
      })
      .catch(() => {
        setErrorMsg("Duplicate check failed. Please try again.");
        setPhase("error");
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (isCompleted && task?.result) {
      const result = task.result as { result: string; confidence: number };
      if (result.result === "DUPLICATE") {
        setPhase("duplicate");
      } else {
        setPhase("complete");
      }
    }
    if (isFailed) {
      setErrorMsg(task?.error_message ?? "Duplicate check failed.");
      setPhase("error");
    }
  }, [isCompleted, isFailed]); // eslint-disable-line react-hooks/exhaustive-deps

  const steps = [
    {
      key: "db_scan",
      icon: Database,
      title: "Database Fuzzy Match",
      description: "Scanning existing profiles using email, phone, and name similarity (pg_trgm)",
    },
    {
      key: "ai_compare",
      icon: Brain,
      title: "AI Semantic Comparison",
      description: "Claude analyzes potential matches for name variants, timeline overlap, and experience similarity",
    },
    {
      key: "complete",
      icon: CheckCircle2,
      title: "Verification Complete",
      description: "No duplicate profiles found — your profile is unique",
    },
  ];

  const phaseIndex = ["db_scan", "ai_compare", "complete"].indexOf(phase);

  if (phase === "error") {
    return (
      <>
        <StepHeader step={4} title="Checking for duplicates" description="Verifying your profile is unique." />
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="flex items-center gap-4 py-6">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <div>
              <p className="font-semibold text-destructive">Check failed</p>
              <p className="text-sm text-muted-foreground">{errorMsg}</p>
            </div>
          </CardContent>
        </Card>
      </>
    );
  }

  if (phase === "duplicate") {
    return (
      <>
        <StepHeader step={4} title="Duplicate profile found" description="A profile matching yours already exists." />
        <Card className="border-yellow-200 bg-yellow-50/50">
          <CardContent className="flex items-center gap-4 py-6">
            <AlertCircle className="h-8 w-8 text-yellow-600" />
            <div>
              <p className="font-semibold text-yellow-800">Duplicate Detected</p>
              <p className="text-sm text-yellow-700">
                A candidate profile with similar details already exists. Please contact support if this is incorrect.
              </p>
            </div>
          </CardContent>
        </Card>
      </>
    );
  }

  return (
    <>
      <StepHeader
        step={4}
        title="Checking for duplicates"
        description="We're verifying that your profile doesn't already exist in our system."
      />

      <Card>
        <CardContent className="py-8">
          <div className="space-y-6">
            {steps.map((step, i) => {
              const isActive = step.key === phase || (phase === "complete" && step.key === "complete");
              const isDone =
                i < phaseIndex ||
                (phase === "complete" && step.key !== "complete" ? true : false);
              const isPending = phaseIndex >= 0 && i > phaseIndex && phase !== "complete";
              const Icon = step.icon;

              return (
                <div key={step.key} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div
                      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition-all ${
                        isDone
                          ? "bg-green-100 text-green-600"
                          : isActive
                            ? "bg-primary/10 text-primary"
                            : "bg-muted text-muted-foreground/40"
                      }`}
                    >
                      {isActive && phase !== "complete" ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                      ) : isDone || phase === "complete" ? (
                        <CheckCircle2 className="h-5 w-5" />
                      ) : (
                        <Icon className="h-5 w-5" />
                      )}
                    </div>
                    {i < steps.length - 1 && (
                      <div
                        className={`mt-1 w-0.5 flex-1 min-h-6 transition-colors ${
                          isDone ? "bg-green-300" : "bg-border"
                        }`}
                      />
                    )}
                  </div>
                  <div className="pb-2">
                    <p className={`font-semibold ${isPending ? "text-muted-foreground/40" : ""}`}>
                      {step.title}
                    </p>
                    <p className={`mt-0.5 text-sm ${isPending ? "text-muted-foreground/30" : "text-muted-foreground"}`}>
                      {step.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {phase === "complete" && (
        <div className="mt-6 flex justify-end">
          <Button onClick={() => setStep("id_verification")} size="lg">
            Continue to ID Verification
            <ArrowRight />
          </Button>
        </div>
      )}
    </>
  );
}
