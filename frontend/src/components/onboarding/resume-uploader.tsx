"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, X, Loader2 } from "lucide-react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { useChatStore } from "@/stores/chat-store";
import { messages } from "@/lib/message-templates";
import { mockDelay, mockResumeParseResult } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function ResumeUploader() {
  const { setStep, updateCandidateData } = useOnboardingStore();
  const { addMessage, setIsTyping } = useChatStore();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) setSelectedFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "image/*": [".png", ".jpg", ".jpeg"],
    },
    maxSize: 10 * 1024 * 1024,
    maxFiles: 1,
    disabled: isProcessing,
  });

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    addMessage({ sender: "user", type: "text", content: `Uploaded: ${selectedFile.name}` });
    addMessage({ sender: "bot", type: "processing", content: messages.resumeParsing });
    setIsTyping(true);

    // Simulate AI processing with progressive delay
    await mockDelay(3000);

    const result = mockResumeParseResult;
    updateCandidateData({ parsedResume: result });
    setIsTyping(false);
    addMessage({ sender: "bot", type: "text", content: messages.resumeParseSuccess });
    addMessage({
      sender: "bot",
      type: "data-card",
      data: {
        full_name: result.full_name,
        email: result.email,
        total_experience_years: result.total_experience_years,
        primary_domain: result.primary_domain,
        confidence: result.confidence_score,
      },
    });
    addMessage({
      sender: "bot",
      type: "skill-tags",
      data: { skills: result.skills_normalized },
    });

    await mockDelay(500);
    setStep("resume_review");
    setIsProcessing(false);
  };

  return (
    <div className="space-y-3">
      <Card
        {...getRootProps()}
        className={`cursor-pointer border-2 border-dashed transition-colors ${
          isDragActive
            ? "border-primary bg-primary/5"
            : isProcessing
              ? "cursor-not-allowed border-muted"
              : "border-border hover:border-primary/50 hover:bg-primary/5"
        }`}
      >
        <CardContent className="flex flex-col items-center justify-center py-10 text-center">
          <input {...getInputProps()} />
          <Upload className={`mb-3 h-10 w-10 ${isDragActive ? "text-primary" : "text-muted-foreground"}`} />
          {isDragActive ? (
            <p className="font-medium text-primary">Drop your resume here</p>
          ) : (
            <>
              <p className="font-medium">Drag & drop your resume, or click to browse</p>
              <p className="mt-1 text-sm text-muted-foreground">PDF, DOCX, or Image • Max 10MB</p>
            </>
          )}
        </CardContent>
      </Card>

      {selectedFile && !isProcessing && (
        <Card>
          <CardContent className="flex items-center justify-between py-4">
            <div className="flex items-center gap-3">
              <FileText className="h-6 w-6 text-primary" />
              <div>
                <p className="font-medium">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <Button variant="ghost" size="icon-sm" onClick={() => setSelectedFile(null)}>
              <X className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      )}

      {selectedFile && !isProcessing && (
        <Button onClick={handleUpload} className="w-full" size="lg">
          Analyze Resume
        </Button>
      )}

      {isProcessing && (
        <div className="flex items-center justify-center gap-2 py-4 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>AI is analyzing your resume...</span>
        </div>
      )}
    </div>
  );
}
