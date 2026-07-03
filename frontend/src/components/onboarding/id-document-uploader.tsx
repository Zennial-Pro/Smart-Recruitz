"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { ShieldCheck, Loader2, FileImage, X } from "lucide-react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { useChatStore } from "@/stores/chat-store";
import { messages } from "@/lib/message-templates";
import { mockDelay, mockVerificationResult } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const DOC_TYPES = [
  { value: "AADHAAR_CARD", label: "Aadhaar Card" },
  { value: "PAN_CARD", label: "PAN Card" },
  { value: "PASSPORT", label: "Passport" },
];

export function IdDocumentUploader() {
  const { setStep } = useOnboardingStore();
  const { addMessage, setIsTyping } = useChatStore();
  const [docType, setDocType] = useState("AADHAAR_CARD");
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/webp": [".webp"],
      "application/pdf": [".pdf"],
    },
    maxSize: 5 * 1024 * 1024,
    maxFiles: 1,
    disabled: isProcessing,
    noClick: !!file, // disable click when file already selected
  });

  const handleVerify = async () => {
    if (!file) return;
    setIsProcessing(true);

    const docLabel = DOC_TYPES.find((d) => d.value === docType)?.label;
    addMessage({ sender: "user", type: "text", content: `Uploaded ${docLabel}: ${file.name}` });
    addMessage({ sender: "bot", type: "processing", content: messages.idVerifying });
    setIsTyping(true);

    await mockDelay(4000);

    setIsTyping(false);
    addMessage({ sender: "bot", type: "text", content: messages.idVerified });
    addMessage({ sender: "bot", type: "verification", data: mockVerificationResult });

    await mockDelay(1000);
    addMessage({ sender: "bot", type: "processing", content: messages.questionsGenerating });
    setStep("interview_prep");
    setIsProcessing(false);
  };

  return (
    <div className="space-y-3">
      {/* Document type selector */}
      <div className="flex gap-2">
        {DOC_TYPES.map((dt) => (
          <Button
            key={dt.value}
            variant={docType === dt.value ? "default" : "outline"}
            size="sm"
            onClick={() => setDocType(dt.value)}
            disabled={isProcessing}
            className="flex-1"
          >
            {dt.label}
          </Button>
        ))}
      </div>

      {/* Drop zone — only show when no file selected */}
      {!file && !isProcessing && (
        <Card
          {...getRootProps()}
          className={`cursor-pointer border-2 border-dashed transition-colors ${
            isDragActive
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary/50"
          }`}
        >
          <CardContent className="flex flex-col items-center justify-center py-10 text-center">
            <input {...getInputProps()} />
            <ShieldCheck className="mb-3 h-10 w-10 text-muted-foreground" />
            <p className="font-medium">Upload your ID document</p>
            <p className="mt-1 text-sm text-muted-foreground">PNG, JPG, PDF • Max 5MB</p>
          </CardContent>
        </Card>
      )}

      {/* File selected — show file info + verify button */}
      {file && !isProcessing && (
        <>
          <Card>
            <CardContent className="flex items-center justify-between py-4">
              <div className="flex items-center gap-3">
                <FileImage className="h-6 w-6 text-primary" />
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB • {DOC_TYPES.find((d) => d.value === docType)?.label}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="icon-sm" onClick={() => setFile(null)}>
                <X className="h-4 w-4" />
              </Button>
            </CardContent>
          </Card>

          <Button onClick={handleVerify} className="w-full" size="lg">
            Verify Identity
          </Button>
        </>
      )}

      {/* Processing state */}
      {isProcessing && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-muted-foreground">Verifying your document...</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
