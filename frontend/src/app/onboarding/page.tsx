"use client";

import { useEffect, useState } from "react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { ChatOnboarding } from "@/components/chat/chat-onboarding";

export default function OnboardingPage() {
  const [mounted, setMounted] = useState(false);
  const sessionKey = useOnboardingStore((s) => s.sessionKey);

  useEffect(() => {
    const result = useOnboardingStore.persist.rehydrate();
    if (result && typeof result.then === "function") {
      result.then(() => setMounted(true));
    } else {
      setMounted(true);
    }
  }, []);

  if (!mounted) return null;

  return <ChatOnboarding key={sessionKey} />;
}
