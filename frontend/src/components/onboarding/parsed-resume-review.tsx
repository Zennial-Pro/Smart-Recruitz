"use client";

import { useOnboardingStore } from "@/stores/onboarding-store";
import { useChatStore } from "@/stores/chat-store";
import { messages } from "@/lib/message-templates";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function ParsedResumeReview() {
  const { candidateData, setStep } = useOnboardingStore();
  const { addMessage } = useChatStore();
  const parsed = candidateData.parsedResume as Record<string, unknown> | undefined;

  if (!parsed) return <Card><CardContent className="py-8 text-center text-sm text-muted-foreground">No parsed data.</CardContent></Card>;

  const experience = (parsed.experience ?? []) as Array<Record<string, unknown>>;
  const education = (parsed.education ?? []) as Array<Record<string, unknown>>;

  const handleConfirm = () => {
    addMessage({ sender: "user", type: "text", content: "Looks good, proceed!" });
    addMessage({ sender: "bot", type: "text", content: messages.resumeReviewComplete });
    addMessage({ sender: "bot", type: "processing", content: messages.duplicateChecking });
    setStep("duplicate_check");
  };

  return (
    <div className="space-y-3">
      {experience.length > 0 && (
        <Card>
          <CardHeader className="pb-3"><CardTitle className="text-sm">Experience</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {experience.map((exp, i) => (
              <div key={i} className="border-l-2 border-primary/30 pl-3">
                <p className="text-sm font-medium">{String(exp.title ?? "")} at {String(exp.company ?? "")}</p>
                <div className="mt-1 flex items-center gap-2">
                  {exp.domain ? <Badge variant="secondary">{String(exp.domain)}</Badge> : null}
                  {exp.duration_months ? <span className="text-xs text-muted-foreground">{String(exp.duration_months)} months</span> : null}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
      {education.length > 0 && (
        <Card>
          <CardHeader className="pb-3"><CardTitle className="text-sm">Education</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {education.map((edu, i) => (
              <div key={i}>
                <p className="text-sm font-medium">{String(edu.degree ?? "")} — {String(edu.institution ?? "")}</p>
                {edu.graduation_year ? <p className="text-xs text-muted-foreground">Class of {String(edu.graduation_year)}</p> : null}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
      <Button onClick={handleConfirm} className="w-full" size="lg"><Check />Confirm & Continue</Button>
    </div>
  );
}
