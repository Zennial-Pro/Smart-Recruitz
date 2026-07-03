"use client";

import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import { ShieldCheck, Loader2, FileImage, X, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { api } from "@/lib/api-client";
import { useTaskPolling } from "@/hooks/use-task-polling";
import type { TaskCreatedResponse } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { StepHeader } from "@/components/wizard/step-header";

type Phase = "select" | "verifying" | "verified" | "failed";

const DOC_TYPES = [
  { value: "AADHAAR_CARD", label: "Aadhaar Card", description: "12-digit unique identity" },
  { value: "PAN_CARD", label: "PAN Card", description: "Permanent account number" },
  { value: "PASSPORT", label: "Passport", description: "Government-issued travel doc" },
];

interface VerificationResult {
  status: string;
  confidence_score: number;
  document_type: string;
  extracted_data: Record<string, string>;
  data_match_results: Record<string, unknown>;
  flags: string[];
}

export function IdVerificationStep() {
  const { candidateRef, setStep } = useOnboardingStore();
  const [docType, setDocType] = useState("AADHAAR_CARD");
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("select");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { task, isCompleted, isFailed } = useTaskPolling({ taskId });

  useEffect(() => {
    if (isCompleted && task?.result) {
      const vr = task.result as unknown as VerificationResult;
      setResult(vr);
      if (vr.status === "VERIFIED") setPhase("verified");
      else setPhase("failed");
    }
    if (isFailed) {
      setError(task?.error_message ?? "Verification failed. Please try again.");
      setPhase("select");
      setTaskId(null);
    }
  }, [isCompleted, isFailed]); // eslint-disable-line react-hooks/exhaustive-deps

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
      "application/pdf": [".pdf"],
    },
    maxSize: 5 * 1024 * 1024,
    maxFiles: 1,
    disabled: phase !== "select",
  });

  const handleVerify = async () => {
    if (!file || !candidateRef) return;
    setError(null);
    setPhase("verifying");

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("candidate_ref", candidateRef);
      formData.append("doc_type", docType);

      const res = await api
        .post("agent3/verify-identity", { body: formData })
        .json<TaskCreatedResponse>();
      setTaskId(res.task_id);
    } catch {
      setError("Failed to upload document. Please try again.");
      setPhase("select");
    }
  };

  return (
    <>
      <StepHeader
        step={5}
        title="Identity verification"
        description="Upload a government-issued ID document for verification. We only check internal consistency — no external database calls."
      />

      {phase === "select" && (
        <div className="space-y-6">
          <div>
            <p className="mb-3 text-sm font-medium text-muted-foreground">Select document type</p>
            <div className="grid gap-3 sm:grid-cols-3">
              {DOC_TYPES.map((dt) => (
                <button
                  key={dt.value}
                  onClick={() => setDocType(dt.value)}
                  className={`rounded-xl border-2 p-4 text-left transition-all ${
                    docType === dt.value
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/30"
                  }`}
                >
                  <p className="font-semibold">{dt.label}</p>
                  <p className="mt-0.5 text-sm text-muted-foreground">{dt.description}</p>
                </button>
              ))}
            </div>
          </div>

          {!file ? (
            <Card
              {...getRootProps()}
              className={`cursor-pointer border-2 border-dashed transition-all ${
                isDragActive
                  ? "border-primary bg-primary/5 scale-[1.01]"
                  : "border-border hover:border-primary/50"
              }`}
            >
              <CardContent className="flex flex-col items-center justify-center py-14 text-center">
                <input {...getInputProps()} />
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
                  <ShieldCheck className="h-7 w-7 text-primary" />
                </div>
                <p className="text-lg font-semibold">
                  Upload your {DOC_TYPES.find((d) => d.value === docType)?.label}
                </p>
                <p className="mt-1 text-muted-foreground">PNG, JPG, or PDF • Max 5MB</p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-between py-5">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                    <FileImage className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(file.size / 1024 / 1024).toFixed(2)} MB •{" "}
                      {DOC_TYPES.find((d) => d.value === docType)?.label}
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
              <Button onClick={handleVerify} size="lg">
                <ShieldCheck />
                Verify Document
              </Button>
            </div>
          )}
        </div>
      )}

      {phase === "verifying" && (
        <Card>
          <CardContent className="flex flex-col items-center gap-6 py-16">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
            <div className="text-center">
              <p className="text-lg font-semibold">Verifying your document...</p>
              <p className="mt-1 text-muted-foreground">
                Running OCR extraction, tampering detection, and data matching
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {phase === "failed" && (
        <div className="space-y-4">
          <Card className="border-destructive/30 bg-destructive/5">
            <CardContent className="py-6">
              <div className="flex items-start gap-4">
                <AlertCircle className="mt-0.5 h-8 w-8 shrink-0 text-destructive" />
                <div>
                  <p className="font-semibold text-destructive">Document Verification Failed</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {result?.flags?.length
                      ? `Issues found: ${result.flags.map((f) => f.replace(/_/g, " ")).join(", ")}.`
                      : "We could not verify this document."}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="py-5">
              <p className="mb-3 font-medium">Please upload a valid document that:</p>
              <ul className="space-y-1.5 text-sm text-muted-foreground">
                <li>• Is an original, unedited government-issued ID (Aadhaar, PAN, Passport)</li>
                <li>• Has your full name clearly visible and matching your registered name</li>
                <li>• Has the ID number fully visible and unobscured</li>
                <li>• Is a clear photo or scan — not blurry, cropped, or dark</li>
                <li>• Has not been digitally edited or altered in any way</li>
              </ul>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={() => { setPhase("select"); setFile(null); setResult(null); }} size="lg" variant="outline">
              Upload Again
            </Button>
          </div>
        </div>
      )}

      {phase === "verified" && result && (
        <div className="space-y-6">
          <Card className="border-green-200 bg-green-50/50">
            <CardContent className="flex items-center gap-4 py-5">
              <CheckCircle2 className="h-8 w-8 text-green-600" />
              <div>
                <p className="text-lg font-semibold text-green-800">Identity Verified</p>
                <p className="text-sm text-green-700">
                  Document authenticated with {Math.round(result.confidence_score * 100)}% confidence
                </p>
              </div>
              <Badge variant="default" className="ml-auto">VERIFIED</Badge>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <h3 className="mb-3 font-semibold">Confidence Score</h3>
              <div className="flex items-center gap-4">
                <Progress value={result.confidence_score * 100} className="h-3 flex-1" />
                <span className="text-2xl font-bold">
                  {Math.round(result.confidence_score * 100)}%
                </span>
              </div>
            </CardContent>
          </Card>

          {Object.keys(result.extracted_data).length > 0 && (
            <Card>
              <CardContent>
                <h3 className="mb-4 font-semibold">Extracted Data</h3>
                <div className="grid gap-4 sm:grid-cols-3">
                  {Object.entries(result.extracted_data).map(([key, val]) => (
                    <div key={key} className="rounded-lg bg-muted/50 p-3">
                      <p className="text-xs uppercase tracking-wider text-muted-foreground">
                        {key.replace(/_/g, " ")}
                      </p>
                      <p className="mt-1 font-semibold">{val}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <div className="flex justify-end">
            <Button onClick={() => setStep("interview_prep")} size="lg">
              Continue to Interview Prep
              <ArrowRight />
            </Button>
          </div>
        </div>
      )}
    </>
  );
}
