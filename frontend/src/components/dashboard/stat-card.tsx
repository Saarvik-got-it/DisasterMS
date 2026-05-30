import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function StatCard({
  title,
  value,
  description,
}: {
  title: string
  value: string
  description?: string
}) {
  return (
    <Card className="rounded-2xl border-border/60 bg-card/95 shadow-sm">
      <CardHeader className="space-y-2">
        <CardTitle className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          {title}
        </CardTitle>
        <div className="text-2xl font-semibold text-foreground">{value}</div>
      </CardHeader>
      {description ? (
        <CardContent className="text-sm text-muted-foreground">
          {description}
        </CardContent>
      ) : null}
    </Card>
  )
}
