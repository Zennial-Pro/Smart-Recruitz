"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { registrationSchema, type RegistrationFormData } from "@/lib/validators";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { useChatStore } from "@/stores/chat-store";
import { messages } from "@/lib/message-templates";
import { mockDelay } from "@/lib/mock-data";
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function RegistrationForm() {
  const { setCandidateRef, setStep, updateCandidateData } = useOnboardingStore();
  const { addMessage, setIsTyping } = useChatStore();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<RegistrationFormData>({
    resolver: zodResolver(registrationSchema),
  });

  const onSubmit = async (data: RegistrationFormData) => {
    setIsSubmitting(true);
    addMessage({ sender: "user", type: "text", content: `${data.full_name} • ${data.email} • ${data.phone}` });
    setIsTyping(true);
    await mockDelay(1500);
    const ref = `SR-2024-${String(Math.floor(Math.random() * 99999)).padStart(5, "0")}`;
    setCandidateRef(ref);
    updateCandidateData(data);
    setIsTyping(false);
    addMessage({ sender: "bot", type: "text", content: messages.registrationSuccess });
    setStep("resume_upload");
    setIsSubmitting(false);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Your Details</CardTitle>
        <CardDescription>We need some basic info to get started</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="full_name">Full Name</Label>
            <Input id="full_name" placeholder="John Doe" {...register("full_name")} />
            {errors.full_name && <p className="text-xs text-destructive">{errors.full_name.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="john@example.com" {...register("email")} />
            {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">Phone</Label>
            <Input id="phone" type="tel" placeholder="+91 98765 43210" {...register("phone")} />
            {errors.phone && <p className="text-xs text-destructive">{errors.phone.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="target_role">Target Role <span className="text-muted-foreground">(optional)</span></Label>
            <Input id="target_role" placeholder="Senior Python Developer" {...register("target_role")} />
          </div>
          <Button type="submit" disabled={isSubmitting} className="w-full" size="lg">
            {isSubmitting ? <><Loader2 className="animate-spin" />Registering...</> : "Continue"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
