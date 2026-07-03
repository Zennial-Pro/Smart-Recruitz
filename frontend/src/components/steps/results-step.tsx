"use client";

import { useEffect, useState } from "react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { useTaskPolling } from "@/hooks/use-task-polling";
import { Loader2, Trophy, XCircle, ArrowRight, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { StepHeader } from "@/components/wizard/step-header";

interface ScoringResult {
  overall_score: number;
  l1_status: string;
  recommendation: string;
  evaluation: Record<string, { score: number; assessment: string }>;
  answer_validation: { question: string; answer?: string; answer_quality: string; score: number }[];
}

export function ResultsStep() {
  const { candidateData, setStep } = useOnboardingStore();
  const [data, setData] = useState<ScoringResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const taskId = candidateData.scoringTaskId ?? null;
  const { task, isCompleted, isFailed } = useTaskPolling({ taskId });

  useEffect(() => {
    if (isCompleted && task?.result) {
      setData(task.result as unknown as ScoringResult);
    }
    if (isFailed) {
      setError(task?.error_message ?? "Scoring failed. Please try again.");
    }
  }, [isCompleted, isFailed]); // eslint-disable-line react-hooks/exhaustive-deps

  if (error) {
    return (
      <>
        <StepHeader step={7} title="Results" description="" />
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="py-6 text-destructive">{error}</CardContent>
        </Card>
      </>
    );
  }

  if (!data) {
    return (
      <>
        <StepHeader step={7} title="Evaluating your interview" description="Our AI is scoring your responses..." />
        <Card>
          <CardContent className="flex flex-col items-center gap-6 py-16">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
              <Brain className="h-8 w-8 animate-pulse text-primary" />
            </div>
            <p className="text-lg font-semibold">Scoring in progress...</p>
            <p className="text-muted-foreground text-sm">Evaluating technical accuracy, communication, and experience depth</p>
          </CardContent>
        </Card>
      </>
    );
  }

  const passed = data.l1_status === "PASSED";

  return (
    <>
      <StepHeader step={7} title="Your results" description="Here's how you performed in the AI-assisted interview evaluation." />

      <div className="space-y-6">
        <Card className={passed ? "border-green-200 bg-green-50/30" : "border-destructive/30 bg-destructive/5"}>
          <CardContent className="flex items-center gap-8 py-8">
            {passed ? <Trophy className="h-12 w-12 text-green-600" /> : <XCircle className="h-12 w-12 text-destructive" />}
            <div className="flex-1">
              <div className="flex items-baseline gap-3">
                <span className={`text-5xl font-bold ${passed ? "text-green-700" : "text-destructive"}`}>
                  {data.overall_score}%
                </span>
                <Badge variant={passed ? "default" : "destructive"}>{data.l1_status}</Badge>
              </div>
              <p className="mt-1 text-muted-foreground">{data.recommendation.replace(/_/g, " ")}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <h3 className="mb-6 text-lg font-semibold">Score Breakdown</h3>
            <div className="space-y-5">
              {Object.entries(data.evaluation).map(([category, ev]) => (
                <div key={category}>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="font-medium capitalize">{category.replace(/_/g, " ")}</span>
                    <span className={`text-lg font-bold ${ev.score >= 60 ? "text-green-600" : "text-destructive"}`}>{ev.score}%</span>
                  </div>
                  <Progress value={ev.score} className="h-3" />
                  <p className="mt-1 text-sm text-muted-foreground">{ev.assessment}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold">Answer Details</h3>
          {data.answer_validation.map((av, i) => (
            <Card key={i}>
              <CardContent className="py-5 space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex gap-3">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold">{i + 1}</span>
                    <p className="font-medium leading-snug">{av.question}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Badge variant={av.answer_quality === "CORRECT" ? "default" : av.answer_quality === "PARTIAL" ? "secondary" : "destructive"}>
                      {av.answer_quality}
                    </Badge>
                    <span className={`text-sm font-bold ${av.score >= 60 ? "text-green-600" : "text-destructive"}`}>{av.score}%</span>
                  </div>
                </div>
                {av.answer && (
                  <div className="ml-10 rounded-lg bg-muted/50 p-3">
                    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Your Answer</p>
                    <p className="text-sm text-muted-foreground">{av.answer}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {passed && (
          <div className="flex justify-end">
            <Button onClick={() => setStep("talent_pool")} size="lg">
              Enter Talent Pool
              <ArrowRight />
            </Button>
          </div>
        )}
      </div>
    </>
  );
}
