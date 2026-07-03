"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Star, Users, Bell } from "lucide-react";

export function TalentPoolStep() {
  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="text-center">
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-green-100">
          <CheckCircle2 className="h-10 w-10 text-green-600" />
        </div>
        <h1 className="text-3xl font-bold">Welcome to the Talent Pool!</h1>
        <p className="mx-auto mt-2 max-w-lg text-lg text-muted-foreground">
          Your verified profile is now visible to hiring managers. We'll notify you when there's a match.
        </p>
        <Badge variant="default" className="mt-4 text-base px-4 py-1.5">
          VERIFIED CANDIDATE
        </Badge>
      </div>

      {/* What happens next */}
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          {
            icon: Star,
            title: "Profile Ranked",
            description: "Your skills and experience are indexed for hiring manager searches.",
          },
          {
            icon: Users,
            title: "Matched to Roles",
            description: "Our system matches your profile to open positions automatically.",
          },
          {
            icon: Bell,
            title: "Get Notified",
            description: "You'll receive alerts when a hiring manager shows interest.",
          },
        ].map((item) => (
          <Card key={item.title}>
            <CardContent className="flex flex-col items-center py-8 text-center">
              <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
                <item.icon className="h-6 w-6 text-primary" />
              </div>
              <p className="font-semibold">{item.title}</p>
              <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
