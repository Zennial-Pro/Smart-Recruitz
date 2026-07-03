"use client";

import { useEffect, useState } from "react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { useChatStore } from "@/stores/chat-store";
import { messages } from "@/lib/message-templates";
import { mockDelay, mockScoringResult } from "@/lib/mock-data";
import { ScoreDashboard } from "@/components/onboarding/score-dashboard";
import { Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function ScoreResults() {
  const { setStep } = useOnboardingStore();
  const { addMessage, setIsTyping } = useChatStore();
  const [scoreData, setScoreData] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function runScoring() {
      setIsTyping(true);
      addMessage({ sender: "bot", type: "processing", content: messages.scoringInterview });

      // Simulate AI scoring
      await mockDelay(5000);
      if (cancelled) return;

      setIsTyping(false);
      setScoreData(mockScoringResult);
      addMessage({ sender: "bot", type: "text", content: messages.scoringComplete });

      await mockDelay(1000);
      if (cancelled) return;

      if (mockScoringResult.overall_score >= 60) {
        addMessage({ sender: "bot", type: "text", content: messages.talentPoolWelcome });
        setStep("talent_pool");
      } else {
        addMessage({ sender: "bot", type: "text", content: messages.interviewFailed });
      }
    }

    runScoring();
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (!scoreData) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-4 py-10">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <div className="text-center">
            <p className="font-medium">Evaluating your interview...</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Scoring responses against expected answer points
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return <ScoreDashboard data={scoreData} />;
}
