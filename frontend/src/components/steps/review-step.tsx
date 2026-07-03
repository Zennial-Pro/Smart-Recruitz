"use client";

import { useOnboardingStore } from "@/stores/onboarding-store";
import { ArrowRight, Pencil, Check, Mail, Phone, Briefcase, GraduationCap, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { StepHeader } from "@/components/wizard/step-header";

export function ReviewStep() {
  const { candidateData, setStep } = useOnboardingStore();
  const parsed = candidateData.parsedResume as Record<string, unknown> | undefined;

  if (!parsed) {
    return <p className="text-muted-foreground">No data to review. Please go back.</p>;
  }

  const name = parsed.full_name as string;
  const email = (parsed.email as string) || candidateData.email;
  const phone = (parsed.phone as string) || candidateData.phone;
  const title = parsed.current_title as string;
  const domain = parsed.primary_domain as string;
  const skills = (parsed.skills_normalized as { standard_name: string; proficiency: string }[]) ?? [];
  const experience = (parsed.experience as { company: string; title: string; domain: string; start_date: string; end_date: string; duration_months: number; is_current: boolean }[]) ?? [];
  const education = (parsed.education as { institution: string; degree: string; field: string; graduation_year: number | null }[]) ?? [];

  const totalMonths = experience.reduce((sum, e) => sum + e.duration_months, 0);
  const expDisplay = totalMonths < 12
    ? `${totalMonths} month${totalMonths !== 1 ? "s" : ""}`
    : `${(totalMonths / 12).toFixed(1)} years`;

  return (
    <>
      <StepHeader
        step={3}
        title="Review your profile"
        description="Please verify that the extracted information is correct before proceeding."
      />

      <div className="space-y-6">
        {/* Profile header */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-2xl font-bold text-primary">
                {name?.charAt(0)?.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-xl font-bold">{name}</h3>
                {title && <p className="text-muted-foreground">{title}</p>}
                <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-sm text-muted-foreground">
                  {email && (
                    <span className="flex items-center gap-1.5">
                      <Mail className="h-3.5 w-3.5" />
                      {email}
                    </span>
                  )}
                  {phone && (
                    <span className="flex items-center gap-1.5">
                      <Phone className="h-3.5 w-3.5" />
                      {phone}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <Separator className="my-5" />

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">Experience</p>
                <p className="mt-1 font-semibold">{expDisplay}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">Domain</p>
                <p className="mt-1 font-semibold">{domain || "—"}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">Skills</p>
                <p className="mt-1 font-semibold">{skills.length} identified</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Skills */}
        {skills.length > 0 && (
          <Card>
            <CardContent>
              <h4 className="mb-3 font-semibold">Skills</h4>
              <div className="flex flex-wrap gap-2">
                {skills.map((s) => (
                  <Badge
                    key={s.standard_name}
                    variant={
                      s.proficiency === "EXPERT" || s.proficiency === "ADVANCED"
                        ? "default"
                        : s.proficiency === "INTERMEDIATE"
                          ? "secondary"
                          : "outline"
                    }
                    className="gap-1.5 py-1"
                  >
                    {s.standard_name}
                    <span className="text-[10px] opacity-60">{s.proficiency}</span>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Experience */}
        {experience.length > 0 && (
          <Card>
            <CardContent>
              <h4 className="mb-4 font-semibold flex items-center gap-2">
                <Briefcase className="h-4 w-4" /> Experience
              </h4>
              <div className="space-y-4">
                {experience.map((exp, i) => (
                  <div key={i} className="flex gap-3">
                    <div className="flex flex-col items-center pt-1">
                      <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                      {i < experience.length - 1 && <div className="mt-1 w-0.5 flex-1 bg-border" />}
                    </div>
                    <div className="pb-3">
                      <p className="font-semibold">{exp.title}</p>
                      <p className="text-sm text-muted-foreground">{exp.company}</p>
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        {exp.domain && <Badge variant="secondary" className="text-xs">{exp.domain}</Badge>}
                        {(exp.start_date || exp.end_date) && (
                          <span className="text-xs text-muted-foreground">
                            {exp.start_date} — {exp.is_current ? "Present" : exp.end_date}
                          </span>
                        )}
                        <span className="text-xs text-muted-foreground">
                          ({exp.duration_months < 12
                            ? `${exp.duration_months} mo`
                            : `${Math.floor(exp.duration_months / 12)} yr${exp.duration_months % 12 > 0 ? ` ${exp.duration_months % 12} mo` : ""}`})
                        </span>
                        {exp.is_current && <Badge variant="default" className="text-xs">Current</Badge>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Education */}
        {education.length > 0 && (
          <Card>
            <CardContent>
              <h4 className="mb-4 font-semibold flex items-center gap-2">
                <GraduationCap className="h-4 w-4" /> Education
              </h4>
              <div className="space-y-3">
                {education.map((edu, i) => (
                  <div key={i}>
                    <p className="font-semibold">{edu.degree}{edu.field ? ` in ${edu.field}` : ""}</p>
                    <p className="text-sm text-muted-foreground">
                      {edu.institution}{edu.graduation_year ? ` • ${edu.graduation_year}` : ""}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <div className="flex items-center justify-between">
          <Button variant="outline" size="lg" onClick={() => setStep("resume_upload")}>
            <Pencil />
            Re-upload Resume
          </Button>
          <Button size="lg" onClick={() => setStep("duplicate_check")}>
            <Check />
            Looks Good — Continue
            <ArrowRight />
          </Button>
        </div>
      </div>
    </>
  );
}
