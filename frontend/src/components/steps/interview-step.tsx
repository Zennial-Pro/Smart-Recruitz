"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { api } from "@/lib/api-client";
import { useTaskPolling } from "@/hooks/use-task-polling";
import type { TaskCreatedResponse } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Loader2, Clock, Sparkles, AlertCircle,
  Video, Mic, CheckCircle2, ChevronRight,
} from "lucide-react";
import { StepHeader } from "@/components/wizard/step-header";

interface Question {
  q_id: string;
  category: string;
  question: string;
  targets_skill?: string;
  difficulty: string;
  expected_answer_points?: string[];
  time_estimate_seconds: number;
}

type Phase = "loading" | "error" | "intro" | "recording" | "transcribing" | "retry" | "done";

function formatTime(secs: number) {
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function InterviewStep() {
  const { candidateRef, setStep, updateCandidateData, candidateData } = useOnboardingStore();

  // Question generation
  const [questions, setQuestions] = useState<Question[]>([]);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { task, isCompleted, isFailed } = useTaskPolling({ taskId });

  // Interview flow
  const [phase, setPhase] = useState<Phase>("loading");
  const [currentIdx, setCurrentIdx] = useState(0);
  const [transcripts, setTranscripts] = useState<{ q_id: string; question: string; answer: string }[]>([]);

  // Recording
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const [recording, setRecording] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Generate questions on mount
  useEffect(() => {
    if (!candidateRef) return;
    api
      .post("agent4/generate-questions", { searchParams: { candidate_ref: candidateRef } })
      .json<TaskCreatedResponse>()
      .then((res) => setTaskId(res.task_id))
      .catch(() => setError("Failed to generate questions. Please try again."));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (isCompleted && task?.result) {
      const res = task.result as { interview_ref: string; questions: Question[] };
      setQuestions(res.questions ?? []);
      updateCandidateData({ interviewRef: res.interview_ref });
      setPhase("intro");
    }
    if (isFailed) {
      setError(task?.error_message ?? "Question generation failed.");
      setPhase("error");
    }
  }, [isCompleted, isFailed]); // eslint-disable-line react-hooks/exhaustive-deps

  const currentQ = questions[currentIdx];

  // Start camera
  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
    } catch {
      setError("Camera/microphone access denied. Please allow access and try again.");
      setPhase("error");
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  // Start recording full video/webm (valid container) — backend extracts audio via ffmpeg
  const startRecording = useCallback(() => {
    if (!streamRef.current) return;
    chunksRef.current = [];
    const mimeType = ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm", "video/mp4"]
      .find((m) => MediaRecorder.isTypeSupported(m)) ?? "";
    const mr = new MediaRecorder(streamRef.current, mimeType ? { mimeType } : {});
    console.log("MediaRecorder mimeType:", mr.mimeType);
    mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
    mr.start(1000);
    mediaRecorderRef.current = mr;
    setRecording(true);

    const totalSecs = currentQ.time_estimate_seconds;
    setTimeLeft(totalSecs);
    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current!);
          stopRecording();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, [currentQ]); // eslint-disable-line react-hooks/exhaustive-deps

  // Stop recording and transcribe
  const stopRecording = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    const mr = mediaRecorderRef.current;
    if (!mr || mr.state === "inactive") return;

    mr.onstop = async () => {
      setRecording(false);
      setPhase("transcribing");

      const blob = new Blob(chunksRef.current, { type: "video/webm" });
      const formData = new FormData();
      formData.append("file", blob, `answer_${currentQ.q_id}.webm`);
      formData.append("question_id", currentQ.q_id);

      try {
        const res = await api.post("agent4/transcribe-answer", { body: formData }).json<{ question_id: string; transcript: string }>();
        const newTranscript = {
          q_id: currentQ.q_id,
          question: currentQ.question,
          answer: res.transcript,
        };
        setTranscripts((prev) => [...prev, newTranscript]);

        const isLast = currentIdx >= questions.length - 1;
        if (isLast) {
          stopCamera();
          // Auto-submit to Agent 5
          const fullTranscript = [...transcripts, newTranscript]
            .map((t, i) => `Q${i + 1}: ${t.question}\nAnswer: ${t.answer}`)
            .join("\n\n");
          await api.post("agent5/score-interview", {
            json: {
              candidate_ref: candidateRef,
              interview_ref: candidateData.interviewRef,
              transcript: fullTranscript,
            },
          }).json<TaskCreatedResponse>().then((res) => {
            updateCandidateData({ scoringTaskId: res.task_id });
            setStep("results");
          });
          return;
        } else {
          setCurrentIdx((i) => i + 1);
          setPhase("recording");
          // useEffect handles startRecording for next question
        }
      } catch {
        setPhase("retry");
      }
    };
    mr.stop();
  }, [currentIdx, currentQ, questions.length, startRecording, stopCamera]);

  // When entering recording phase — start camera only on first question, reuse stream for the rest
  useEffect(() => {
    if (phase !== "recording") return;
    if (!streamRef.current) {
      startCamera().then(() => setTimeout(() => startRecording(), 600));
    } else {
      setTimeout(() => startRecording(), 300);
    }
  }, [phase, currentIdx]); // eslint-disable-line react-hooks/exhaustive-deps

  // Submit all transcripts to Agent 5
  // ── Loading ────────────────────────────────────────────────────────────────
  if (phase === "loading") {
    return (
      <>
        <StepHeader step={6} title="Generating interview questions" description="Our AI is creating personalized questions based on your profile." />
        <Card>
          <CardContent className="flex flex-col items-center gap-6 py-16">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
              <Sparkles className="h-8 w-8 animate-pulse text-primary" />
            </div>
            <p className="text-lg font-semibold">Generating personalized questions...</p>
          </CardContent>
        </Card>
      </>
    );
  }

  // ── Error ──────────────────────────────────────────────────────────────────
  if (phase === "error") {
    return (
      <>
        <StepHeader step={6} title="Interview" description="" />
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="flex items-center gap-4 py-6">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      </>
    );
  }

  // ── Intro ──────────────────────────────────────────────────────────────────
  if (phase === "intro") {
    const totalSecs = questions.reduce((s, q) => s + q.time_estimate_seconds, 0);
    return (
      <>
        <StepHeader step={6} title="Video Interview" description={`${questions.length} questions • ~${Math.round(totalSecs / 60)} minutes`} />
        <div className="space-y-6">
          <Card>
            <CardContent className="py-6 space-y-4">
              <p className="font-semibold text-lg">Before you begin</p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2"><CheckCircle2 className="h-4 w-4 mt-0.5 text-green-500 shrink-0" /> Allow camera and microphone access when prompted</li>
                <li className="flex items-start gap-2"><CheckCircle2 className="h-4 w-4 mt-0.5 text-green-500 shrink-0" /> Each question has a timer — recording stops automatically when time is up</li>
                <li className="flex items-start gap-2"><CheckCircle2 className="h-4 w-4 mt-0.5 text-green-500 shrink-0" /> You can also stop recording early once you have answered</li>
                <li className="flex items-start gap-2"><CheckCircle2 className="h-4 w-4 mt-0.5 text-green-500 shrink-0" /> Speak clearly — your answers will be transcribed by AI</li>
                <li className="flex items-start gap-2"><CheckCircle2 className="h-4 w-4 mt-0.5 text-green-500 shrink-0" /> Questions are answered one at a time, no going back</li>
              </ul>
            </CardContent>
          </Card>

          <div className="grid gap-3 sm:grid-cols-3">
            {questions.slice(0, 3).map((q, i) => (
              <Card key={q.q_id}>
                <CardContent className="py-4">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="outline" className="text-xs">{q.category.replace(/_/g, " ")}</Badge>
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <Clock className="h-3 w-3" />{formatTime(q.time_estimate_seconds)}
                    </span>
                  </div>
                  <p className="text-sm font-medium line-clamp-2">{q.question}</p>
                </CardContent>
              </Card>
            ))}
          </div>
          {questions.length > 3 && (
            <p className="text-center text-sm text-muted-foreground">+ {questions.length - 3} more questions</p>
          )}

          <div className="flex justify-end">
            <Button size="lg" onClick={() => setPhase("recording")}>
              <Video className="h-4 w-4" />
              Start Interview
              <ChevronRight />
            </Button>
          </div>
        </div>
      </>
    );
  }

  // ── Recording ──────────────────────────────────────────────────────────────
  if (phase === "recording" && currentQ) {
    const totalSecs = currentQ.time_estimate_seconds;
    const progress = ((totalSecs - timeLeft) / totalSecs) * 100;

    return (
      <>
        <StepHeader
          step={6}
          title={`Question ${currentIdx + 1} of ${questions.length}`}
          description={`${currentQ.category.replace(/_/g, " ")} • ${currentQ.difficulty}`}
        />
        <div className="space-y-4">
          <Card>
            <CardContent className="py-5">
              <p className="text-lg font-semibold leading-snug">{currentQ.question}</p>
              {currentQ.targets_skill && (
                <Badge variant="secondary" className="mt-2">{currentQ.targets_skill}</Badge>
              )}
            </CardContent>
          </Card>

          <Card className="overflow-hidden">
            <div className="relative bg-black aspect-video">
              <video ref={videoRef} autoPlay muted playsInline className="h-full w-full object-cover" />
              {recording && (
                <div className="absolute top-3 left-3 flex items-center gap-2 rounded-full bg-destructive px-3 py-1 text-xs font-semibold text-white">
                  <span className="h-2 w-2 rounded-full bg-white animate-pulse" />
                  REC
                </div>
              )}
              <div className="absolute top-3 right-3 rounded-full bg-black/60 px-3 py-1 text-sm font-mono text-white">
                {formatTime(timeLeft)}
              </div>
            </div>
            <CardContent className="py-3 space-y-2">
              <Progress value={progress} className="h-1.5" />
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  {recording ? "Recording in progress..." : "Initializing camera..."}
                </span>
                {recording && (
                  <Button size="sm" variant="outline" onClick={stopRecording}>
                    <Mic className="h-3.5 w-3.5" />
                    Done Answering
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </>
    );
  }

  // ── Transcribing ───────────────────────────────────────────────────────────
  if (phase === "transcribing") {
    return (
      <>
        <StepHeader step={6} title={`Question ${currentIdx + 1} of ${questions.length}`} description="" />
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-16">
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
            <p className="font-semibold">Transcribing your answer...</p>
            <p className="text-sm text-muted-foreground">This takes a few seconds</p>
          </CardContent>
        </Card>
      </>
    );
  }

  // ── Retry ──────────────────────────────────────────────────────────────────
  if (phase === "retry" && currentQ) {
    return (
      <>
        <StepHeader step={6} title={`Question ${currentIdx + 1} of ${questions.length}`} description="" />
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="py-6 space-y-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-6 w-6 text-destructive shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-destructive">Transcription failed</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Your answer could not be transcribed. Please re-record your answer for this question.
                </p>
              </div>
            </div>
            <div className="rounded-lg bg-muted/50 p-4">
              <p className="text-sm font-medium">{currentQ.question}</p>
            </div>
            <div className="flex justify-end">
              <Button onClick={() => setPhase("recording")}>
                <Video className="h-4 w-4" />
                Re-record This Answer
              </Button>
            </div>
          </CardContent>
        </Card>
      </>
    );
  }

  // ── Done ───────────────────────────────────────────────────────────────────
  if (phase === "done") {
    return (
      <>
        <StepHeader step={6} title="Interview Complete" description="All questions answered. Review your responses below." />
        <div className="space-y-4">
          {transcripts.map((t, i) => (
            <Card key={t.q_id}>
              <CardContent className="py-5 space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Q{i + 1}</p>
                <p className="font-medium">{t.question}</p>
                <div className="rounded-lg bg-muted/50 p-3">
                  <p className="text-sm text-muted-foreground">{t.answer || <span className="italic">No answer transcribed</span>}</p>
                </div>
              </CardContent>
            </Card>
          ))}

        </div>
      </>
    );
  }

  return null;
}
