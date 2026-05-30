import { Badge } from "@/components/ui/badge"

const toneMap: Record<string, string> = {
  LOW: "bg-emerald-100 text-emerald-900",
  MEDIUM: "bg-amber-100 text-amber-900",
  HIGH: "bg-orange-100 text-orange-900",
  CRITICAL: "bg-red-100 text-red-900",
}

export default function StatusPill({ label }: { label: string }) {
  const tone = toneMap[label.toUpperCase()] ?? "bg-muted text-foreground"
  return (
    <Badge className={`rounded-full px-3 py-1 text-xs font-semibold ${tone}`}>
      {label}
    </Badge>
  )
}
