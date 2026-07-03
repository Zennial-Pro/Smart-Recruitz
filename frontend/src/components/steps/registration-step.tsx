"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { registrationSchema, type RegistrationFormData } from "@/lib/validators";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { api } from "@/lib/api-client";
import { useState } from "react";
import { Loader2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { StepHeader } from "@/components/wizard/step-header";

export function RegistrationStep() {
  const { setCandidateRef, setStep, updateCandidateData } = useOnboardingStore();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegistrationFormData>({
    resolver: zodResolver(registrationSchema),
  });

  const onSubmit = async (data: RegistrationFormData) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await api
        .post("candidates/register", { json: data })
        .json<{ candidate_ref: string; status: string }>();
      setCandidateRef(res.candidate_ref);
      updateCandidateData(data);
      setStep("resume_upload");
    } catch {
      setError("Registration failed. Please check your details and try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <StepHeader
        step={1}
        title="Let's get you started"
        description="Enter your basic information to create your candidate profile."
      />

      <Card>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid gap-6 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="full_name">Full Name</Label>
                <Input
                  id="full_name"
                  placeholder="Rahul Kumar"
                  autoComplete="off"
                  {...register("full_name")}
                  aria-invalid={!!errors.full_name}
                />
                {errors.full_name && (
                  <p className="text-sm text-destructive">{errors.full_name.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="rahul@example.com"
                  autoComplete="off"
                  {...register("email")}
                  aria-invalid={!!errors.email}
                />
                {errors.email && (
                  <p className="text-sm text-destructive">{errors.email.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="+91 98765 43210"
                  autoComplete="off"
                  {...register("phone")}
                  aria-invalid={!!errors.phone}
                />
                {errors.phone && (
                  <p className="text-sm text-destructive">{errors.phone.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="target_role">
                  Target Role{" "}
                  <span className="font-normal text-muted-foreground">(optional)</span>
                </Label>
                <Input
                  id="target_role"
                  placeholder="Senior Python Developer"
                  autoComplete="off"
                  {...register("target_role")}
                />
              </div>
            </div>

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}

            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={isSubmitting} size="lg">
                {isSubmitting ? (
                  <>
                    <Loader2 className="animate-spin" />
                    Creating profile...
                  </>
                ) : (
                  <>
                    Continue
                    <ArrowRight />
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </>
  );
}
