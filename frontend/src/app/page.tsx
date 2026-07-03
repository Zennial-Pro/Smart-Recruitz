import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-gradient-to-br from-primary/5 to-background px-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <div className="mx-auto mb-2 flex h-14 w-14 items-center justify-center rounded-xl bg-primary text-xl font-bold text-primary-foreground">
            SR
          </div>
          <CardTitle className="text-2xl">SmartRecruitz</CardTitle>
          <CardDescription>
            Verified Talent Infrastructure — Start your journey to the Talent Pool
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild size="lg" className="w-full">
            <Link href="/onboarding">Begin Onboarding</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
