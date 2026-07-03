"use client";

import { RotateCcw } from "lucide-react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { useChatStore } from "@/stores/chat-store";
import { Button } from "@/components/ui/button";

export function ResetButton() {
  const resetOnboarding = useOnboardingStore((s) => s.reset);
  const clearMessages = useChatStore((s) => s.clearMessages);

  const handleReset = () => {
    resetOnboarding();
    clearMessages();
  };

  return (
    <Button variant="ghost" size="sm" onClick={handleReset} title="Start over">
      <RotateCcw className="h-4 w-4" />
      Restart
    </Button>
  );
}
