import { Trophy, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface ScoreData {
  overall_score?: number; l1_status?: string; recommendation?: string;
  evaluation?: Record<string, { score: number; assessment: string }>;
  answer_validation?: Array<{ question: string; answer_quality: string; score: number }>;
}

export function ScoreDashboard({ data }: { data: Record<string, unknown> }) {
  const sd = data as ScoreData;
  const passed = sd.l1_status === "PASSED";
  const score = sd.overall_score ?? 0;

  return (
    <div className="space-y-3">
      <Card className={passed ? "border-green-200 bg-green-50/50" : "border-destructive/30 bg-destructive/5"}>
        <CardContent className="flex flex-col items-center py-8 text-center">
          {passed ? <Trophy className="mb-2 h-10 w-10 text-green-600" /> : <XCircle className="mb-2 h-10 w-10 text-destructive" />}
          <p className={`text-4xl font-bold ${passed ? "text-green-700" : "text-destructive"}`}>{score}%</p>
          <div className="mt-3 flex items-center gap-2">
            <Badge variant={passed ? "default" : "destructive"}>{sd.l1_status ?? "N/A"}</Badge>
            {sd.recommendation && <Badge variant="secondary">{sd.recommendation.replace(/_/g, " ")}</Badge>}
          </div>
        </CardContent>
      </Card>
      {sd.evaluation && (
        <Card>
          <CardHeader className="pb-3"><CardTitle className="text-sm">Score Breakdown</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(sd.evaluation).map(([category, ev]) => (
              <div key={category}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="capitalize text-muted-foreground">{category.replace(/_/g, " ")}</span>
                  <span className="font-semibold">{ev.score}%</span>
                </div>
                <Progress value={Math.min(ev.score, 100)} />
                <p className="mt-0.5 text-xs text-muted-foreground">{ev.assessment}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
      {sd.answer_validation && sd.answer_validation.length > 0 && (
        <Card>
          <CardHeader className="pb-3"><CardTitle className="text-sm">Answer Details</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {sd.answer_validation.map((av, i) => (
              <div key={i} className="flex items-center gap-3 rounded-lg bg-muted/50 px-3 py-2">
                <span className="text-xs font-medium text-muted-foreground">Q{i + 1}</span>
                <p className="flex-1 truncate text-xs">{av.question}</p>
                <Badge variant={av.answer_quality === "CORRECT" ? "default" : av.answer_quality === "PARTIAL" ? "secondary" : "destructive"}>{av.answer_quality}</Badge>
                <span className="text-xs font-semibold">{av.score}%</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
