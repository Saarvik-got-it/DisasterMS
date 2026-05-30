import { ReactNode } from "react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function SectionCard({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: ReactNode
}) {
  return (
    <Card className="rounded-2xl border-border/60 bg-card/95 shadow-sm">
      <CardHeader className="space-y-1">
        <CardTitle className="text-base font-semibold tracking-tight text-foreground">
          {title}
        </CardTitle>
        {subtitle ? (
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-4">{children}</CardContent>
    </Card>
  )
}
