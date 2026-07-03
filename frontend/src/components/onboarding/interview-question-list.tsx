"use client";

import { useEffect, useState } from "react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { useChatStore } from "@/stores/chat-store";
import { messages } from "@/lib/message-templates";
import { mockDelay, mockQuestions } from "@/lib/mock-data";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Clock, ChevronDown, ChevronUp } from "lucide-react";

interface Question {
  q_id: string;
  category: string;
  question: string;
  targets_skill?: string;
  difficulty: string;
  expected_answer_points?: string[];
  time_estimate_mins?: number;
}

export function InterviewQuestionList() {
  const { setStep, updateCandidateData } = useOnboardingStore();
  const { addMessage, setIsTyping } = useChatStore();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function generate() {
      setIsTyping(true);

      // Simulate AI question generation
      await mockDelay(4000);
      if (cancelled) return;

      setIsTyping(false);
      setLoading(false);
      setQuestions(mockQuestions.questions);
      updateCandidateData({ interviewRef: mockQuestions.interview_ref });
      addMessage({ sender: "bot", type: "text", content: messages.questionsReady });
    }

    generate();
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-4 py-10">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <div className="text-center">
            <p className="font-medium">Generating personalized interview questions...</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Analyzing your skills and experience
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      <Card>
        <CardHeader>
          <CardTitle>Interview Questions ({questions.length})</CardTitle>
          <CardDescription>Review these to prepare for your interview</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {questions.map((q, i) => (
            <div key={q.q_id} className="rounded-lg border bg-muted/30 p-4">
              <button
                onClick={() => setExpanded(expanded === q.q_id ? null : q.q_id)}
                className="flex w-full items-start justify-between gap-3 text-left"
              >
                <div className="flex-1">
                  <p className="font-medium leading-snug">
                    {i + 1}. {q.question}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <Badge
                      variant={
                        q.difficulty === "LEAD"
                          ? "destructive"
                          : q.difficulty === "SENIOR"
                            ? "default"
                            : "secondary"
                      }
                    >
                      {q.difficulty}
                    </Badge>
                    <Badge variant="outline">{q.category.replace(/_/g, " ")}</Badge>
                    {q.targets_skill && (
                      <Badge variant="secondary">{q.targets_skill}</Badge>
                    )}
                    {q.time_estimate_mins && (
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="h-3.5 w-3.5" />
                        {q.time_estimate_mins} min
                      </span>
                    )}
                  </div>
                </div>
                {expanded === q.q_id ? (
                  <ChevronUp className="mt-1 h-5 w-5 shrink-0 text-muted-foreground" />
                ) : (
                  <ChevronDown className="mt-1 h-5 w-5 shrink-0 text-muted-foreground" />
                )}
              </button>

              {expanded === q.q_id && q.expected_answer_points && (
                <div className="mt-3 border-t pt-3">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Expected Answer Points
                  </p>
                  <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                    {q.expected_answer_points.map((pt, j) => (
                      <li key={j}>{pt}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      <Button
        onClick={() => {
          addMessage({ sender: "user", type: "text", content: "I'm ready for the interview" });
          setStep("results");
        }}
        className="w-full"
        size="lg"
      >
        I'm Prepared — Continue
      </Button>
    </div>
  );
}
