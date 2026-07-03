"use client";

import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, X, Loader2, ArrowRight, Sparkles } from "lucide-react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { api } from "@/lib/api-client";
import { useTaskPolling } from "@/hooks/use-task-polling";
import type { TaskCreatedResponse } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { StepHeader } from "@/components/wizard/step-header";

type Phase = "upload" | "analyzing" | "results";

interface ParsedResume {
  full_name: string;
  email: string;
  phone: string;
  current_title: string;
  total_experience_years: number;
  primary_domain: string;
  confidence_score: number;
  skills_normalized: { standard_name: string; proficiency: string }[];
  experience: {
    company: string;
    title: string;
    domain: string;
    start_date: string;
    end_date: string;
    duration_months: number;
    is_current: boolean;
  }[];
  education: {
    institution: string;
    degree: string;
    field: string;
    graduation_year: number | null;
  }[];
}

export function ResumeStep() {
  const { candidateRef, setStep, updateCandidateData } = useOnboardingStore();
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("upload");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [result, setResult] = useState<ParsedResume | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { task, isCompleted, isFailed } = useTaskPolling({ taskId });

  useEffect(() => {
    if (isCompleted && task?.result) {
      const parsed = task.result as unknown as ParsedResume;
      setResult(parsed);
      updateCandidateData({ parsedResume: task.result });
      setPhase("results");
    }
    if (isFailed) {
      setError(task?.error_message ?? "Resume analysis failed. Please try again.");
      setPhase("upload");
      setTaskId(null);
    }
  }, [isCompleted, isFailed]); // eslint-disable-line react-hooks/exhaustive-deps

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/x-pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "image/*": [".png", ".jpg", ".jpeg"],
    },
    maxSize: 10 * 1024 * 1024,
    maxFiles: 1,
    disabled: phase !== "upload",
  });

  const handleAnalyze = async () => {
    if (!file || !candidateRef) return;
    setError(null);
    setPhase("analyzing");

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("candidate_ref", candidateRef);

      const res = await api
        .post("agent1/parse-resume", { body: formData })
        .json<TaskCreatedResponse>();
      setTaskId(res.task_id);
    } catch {
      setError("Failed to upload resume. Please try again.");
      setPhase("upload");
    }
  };

  return (
    <>
      <StepHeader
        step={2}
        title="Upload your resume"
        description="Our AI will analyze your resume and extract your skills, experience, and education."
      />

      {phase === "upload" && (
        <div className="space-y-4">
          <Card
            {...getRootProps()}
            className={`cursor-pointer border-2 border-dashed transition-all ${
              isDragActive
                ? "border-primary bg-primary/5 scale-[1.01]"
                : "border-border hover:border-primary/50 hover:bg-muted/50"
            }`}
          >
            <CardContent className="flex flex-col items-center justify-center py-16 text-center">
              <input {...getInputProps()} />
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              {isDragActive ? (
                <p className="text-lg font-semibold text-primary">Drop your resume here</p>
              ) : (
                <>
                  <p className="text-lg font-semibold">Drag & drop your resume</p>
                  <p className="mt-1 text-muted-foreground">or click to browse files</p>
                  <p className="mt-3 text-sm text-muted-foreground/70">
                    Supports PDF, DOCX, PNG, JPG • Max 10MB
                  </p>
                </>
              )}
            </CardContent>
          </Card>

          {file && (
            <Card>
              <CardContent className="flex items-center justify-between py-4">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                    <FileText className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="icon-sm" onClick={() => setFile(null)}>
                  <X className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}

          {file && (
            <div className="flex justify-end">
              <Button onClick={handleAnalyze} size="lg">
                <Sparkles />
                Analyze with AI
              </Button>
            </div>
          )}
        </div>
      )}

      {phase === "analyzing" && (
        <Card>
          <CardContent className="flex flex-col items-center gap-6 py-16">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
            <div className="w-full max-w-sm space-y-3 text-center">
              <p className="text-lg font-semibold">Analyzing your resume...</p>
              <Progress value={task ? (task.status === "PROCESSING" ? 60 : 20) : 10} className="h-2" />
              <p className="text-sm text-muted-foreground">
                {task?.status === "PROCESSING"
                  ? "Identifying skills and experience..."
                  : "Extracting text and structure..."}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {phase === "results" && result && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-4">
            {[
              { label: "Experience", value: (() => { const m = result.experience.reduce((sum, exp) => sum + exp.duration_months, 0); return m < 12 ? `${m} month${m !== 1 ? "s" : ""}` : `${(m / 12).toFixed(1)} years`; })() },
              { label: "Domain", value: result.primary_domain },
              { label: "Skills", value: `${result.skills_normalized.length} identified` },
              { label: "Confidence", value: `${Math.round(result.confidence_score * 100)}%` },
            ].map((stat) => (
              <Card key={stat.label}>
                <CardContent className="py-4 text-center">
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardContent>
              <h3 className="mb-4 text-lg font-semibold">Skills Identified</h3>
              <div className="flex flex-wrap gap-2">
                {result.skills_normalized.map((skill) => (
                  <Badge
                    key={skill.standard_name}
                    variant={
                      skill.proficiency === "EXPERT" || skill.proficiency === "ADVANCED"
                        ? "default"
                        : skill.proficiency === "INTERMEDIATE"
                          ? "secondary"
                          : "outline"
                    }
                    className="gap-1.5 py-1.5"
                  >
                    {skill.standard_name}
                    <span className="text-[10px] opacity-60">{skill.proficiency}</span>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <h3 className="mb-4 text-lg font-semibold">Experience</h3>
              <div className="space-y-4">
                {result.experience.map((exp, i) => (
                  <div key={i} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className="h-3 w-3 rounded-full bg-primary" />
                      {i < result.experience.length - 1 && (
                        <div className="w-0.5 flex-1 bg-border" />
                      )}
                    </div>
                    <div className="pb-4">
                      <p className="font-semibold">{exp.title}</p>
                      <p className="text-muted-foreground">{exp.company}</p>
                      <div className="mt-1.5 flex flex-wrap items-center gap-2">
                        <Badge variant="secondary">{exp.domain}</Badge>
                        {(exp.start_date || exp.end_date) && (
                          <span className="text-sm text-muted-foreground">
                            {exp.start_date} — {exp.is_current ? "Present" : exp.end_date}
                          </span>
                        )}
                        <span className="text-sm text-muted-foreground">
                          ({exp.duration_months < 12
                            ? `${exp.duration_months} mo`
                            : `${Math.floor(exp.duration_months / 12)} yr${exp.duration_months % 12 > 0 ? ` ${exp.duration_months % 12} mo` : ""}`})
                        </span>
                        {exp.is_current && <Badge variant="default">Current</Badge>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <h3 className="mb-4 text-lg font-semibold">Education</h3>
              {result.education.map((edu, i) => (
                <div key={i}>
                  <p className="font-semibold">{edu.degree} in {edu.field}</p>
                  <p className="text-muted-foreground">
                    {edu.institution} • Class of {edu.graduation_year}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={() => setStep("resume_review")} size="lg">
              Confirm & Continue
              <ArrowRight />
            </Button>
          </div>
        </div>
      )}
    </>
  );
}
