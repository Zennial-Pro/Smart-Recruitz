"use client";

import type { ChatMessage } from "@/stores/chat-store";
import { ProcessingIndicator } from "../shared/processing-indicator";
import { DataCard } from "../shared/data-card";
import { SkillTagsDisplay } from "../onboarding/skill-tags-display";
import { ScoreDashboard } from "../onboarding/score-dashboard";
import { VerificationStatus } from "../onboarding/verification-status";

export function MessageRenderer({ message }: { message: ChatMessage }) {
  const isBot = message.sender === "bot";

  switch (message.type) {
    case "text":
      return (
        <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${isBot ? "self-start bg-muted text-foreground rounded-bl-sm" : "self-end bg-primary text-primary-foreground rounded-br-sm"}`}>
          {message.content}
        </div>
      );
    case "data-card":
      return <div className="max-w-[85%] self-start"><DataCard data={message.data ?? {}} /></div>;
    case "processing":
      return <div className="max-w-[85%] self-start"><ProcessingIndicator message={message.content ?? "Processing..."} /></div>;
    case "skill-tags":
      return <div className="max-w-[90%] self-start"><SkillTagsDisplay skills={(message.data?.skills as Array<{ standard_name: string; proficiency: string }>) ?? []} /></div>;
    case "score-card":
      return <div className="w-full self-start"><ScoreDashboard data={message.data ?? {}} /></div>;
    case "verification":
      return <div className="max-w-[85%] self-start"><VerificationStatus data={message.data ?? {}} /></div>;
    default:
      return <div className="max-w-[85%] self-start rounded-2xl rounded-bl-sm bg-muted px-4 py-3 text-sm">{message.content ?? "..."}</div>;
  }
}
