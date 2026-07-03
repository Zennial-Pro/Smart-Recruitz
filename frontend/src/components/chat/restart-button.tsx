"use client";

import { useOnboardingStore } from "@/stores/onboarding-store";
import { useChatStore } from "@/stores/chat-store";
import { RotateCcw } from "lucide-react";

export function RestartButton() {
  const reset = useOnboardingStore((s) => s.reset);
  const clearMessages = useChatStore((s) => s.clearMessages);

  return (
    <button
      onClick={() => { reset(); clearMessages(); }}
      className="flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold text-violet-500 hover:text-violet-700 hover:bg-violet-50 border border-violet-100 hover:border-violet-200 transition-all"
    >
      <RotateCcw className="h-3.5 w-3.5" />
      Restart
    </button>
  );
}
