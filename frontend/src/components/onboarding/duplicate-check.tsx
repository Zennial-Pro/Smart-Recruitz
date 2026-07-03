"use client";

import { useEffect, useState } from "react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { useChatStore } from "@/stores/chat-store";
import { messages } from "@/lib/message-templates";
import { mockDelay, mockDuplicateResult } from "@/lib/mock-data";
import { Loader2, CheckCircle2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function DuplicateCheck() {
  const { setStep } = useOnboardingStore();
  const { addMessage, setIsTyping } = useChatStore();
  const [phase, setPhase] = useState<"checking" | "done">("checking");

  useEffect(() => {
    let cancelled = false;

    async function runCheck() {
      setIsTyping(true);

      // Simulate DB fuzzy match
      await mockDelay(2000);
      if (cancelled) return;

      // Simulate AI semantic comparison
      await mockDelay(2500);
      if (cancelled) return;

      setIsTyping(false);
      setPhase("done");

      if (mockDuplicateResult.is_duplicate) {
        addMessage({ sender: "bot", type: "text", content: messages.duplicatePossible });
      } else {
        addMessage({ sender: "bot", type: "text", content: messages.duplicateUnique });

        await mockDelay(800);
        if (cancelled) return;
        addMessage({ sender: "bot", type: "text", content: messages.idVerificationPrompt });
        setStep("id_verification");
      }
    }

    runCheck();
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-4 py-10 text-center">
        {phase === "checking" && (
          <>
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
            <div>
              <p className="font-medium">Checking for duplicate profiles...</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Running fuzzy match against our database
              </p>
            </div>
          </>
        )}
        {phase === "done" && (
          <>
            <CheckCircle2 className="h-10 w-10 text-green-500" />
            <p className="font-medium text-green-700">No duplicates found — you're unique!</p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
