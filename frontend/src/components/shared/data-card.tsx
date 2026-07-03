import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function DataCard({ data, title }: { data: Record<string, unknown>; title?: string }) {
  const entries = Object.entries(data).filter(([, v]) => v !== null && v !== undefined && typeof v !== "object");

  return (
    <Card>
      {title && <CardHeader className="pb-2"><CardTitle className="text-sm">{title}</CardTitle></CardHeader>}
      <CardContent className={title ? "" : "pt-4"}>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
          {entries.map(([key, value]) => (
            <div key={key}>
              <dt className="text-xs text-muted-foreground capitalize">{key.replace(/_/g, " ")}</dt>
              <dd className="text-sm font-medium">{String(value)}</dd>
            </div>
          ))}
        </dl>
      </CardContent>
    </Card>
  );
}
