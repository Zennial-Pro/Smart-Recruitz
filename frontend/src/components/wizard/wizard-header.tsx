"use client";

import { useOnboardingStore } from "@/stores/onboarding-store";
import { useChatStore } from "@/stores/chat-store";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { RotateCcw } from "lucide-react";

export function WizardHeader() {
  const { candidateData, reset: resetOnboarding } = useOnboardingStore();
  const clearMessages = useChatStore((s) => s.clearMessages);

  const handleReset = () => {
    resetOnboarding();
    clearMessages();
  };

  return (
    <>
      <header className="flex h-16 items-center justify-between border-b bg-card px-6">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-sm font-bold text-primary-foreground">
            SR
          </div>
          <div>
            <h1 className="text-base font-semibold leading-tight">SmartRecruitz</h1>
            <p className="text-xs text-muted-foreground">Candidate Onboarding Portal</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {candidateData.full_name && (
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium">{candidateData.full_name}</p>
              <p className="text-xs text-muted-foreground">{candidateData.email}</p>
            </div>
          )}
          <Button variant="ghost" size="sm" onClick={handleReset}>
            <RotateCcw className="h-4 w-4" />
            <span className="hidden sm:inline">Restart</span>
          </Button>
        </div>
      </header>
    </>
  );
}
