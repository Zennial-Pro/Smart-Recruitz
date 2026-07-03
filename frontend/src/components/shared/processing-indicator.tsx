import { Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function ProcessingIndicator({ message }: { message: string }) {
  return (
    <Card className="border-amber-200 bg-amber-50/50">
      <CardContent className="flex items-center gap-3 py-3">
        <Loader2 className="h-4 w-4 animate-spin text-amber-600" />
        <span className="text-sm text-amber-800">{message}</span>
      </CardContent>
    </Card>
  );
}
