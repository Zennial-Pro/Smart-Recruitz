import { ShieldCheck, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface VerificationData { status?: string; confidence_score?: number; extracted_data?: Record<string, unknown>; }

export function VerificationStatus({ data }: { data: Record<string, unknown> }) {
  const vd = data as VerificationData;
  const isVerified = vd.status === "VERIFIED";

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          {isVerified ? <ShieldCheck className="h-5 w-5 text-green-600" /> : <ShieldAlert className="h-5 w-5 text-destructive" />}
          <CardTitle className="text-sm">Identity Verification</CardTitle>
          <Badge variant={isVerified ? "default" : "destructive"}>{vd.status ?? "UNKNOWN"}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {vd.confidence_score != null && (
          <div>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Confidence</span>
              <span className="font-semibold">{vd.confidence_score}%</span>
            </div>
            <Progress value={Math.min(vd.confidence_score, 100)} />
          </div>
        )}
        {vd.extracted_data && (
          <div className="rounded-lg bg-muted/50 p-3">
            <p className="mb-1.5 text-xs font-medium text-muted-foreground">Extracted Data</p>
            <dl className="grid grid-cols-2 gap-1">
              {Object.entries(vd.extracted_data).map(([key, val]) => (
                <div key={key}>
                  <dt className="text-[10px] text-muted-foreground capitalize">{key.replace(/_/g, " ")}</dt>
                  <dd className="text-xs font-medium">{String(val)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
