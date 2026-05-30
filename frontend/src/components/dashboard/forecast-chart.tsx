import type { ForecastPoint } from "@/lib/types"

const CHART_HEIGHT = 160
const CHART_WIDTH = 560

function buildPath(points: ForecastPoint[]) {
  if (!points.length) {
    return ""
  }

  const values = points.map((point) => point.rainfall)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  return points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * CHART_WIDTH
      const y = CHART_HEIGHT - ((point.rainfall - min) / range) * CHART_HEIGHT
      return `${index === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(" ")
}

export default function ForecastChart({ points }: { points: ForecastPoint[] }) {
  if (!points.length) {
    return (
      <div className="flex h-40 items-center justify-center rounded-2xl border border-dashed border-border bg-muted/40 text-sm text-muted-foreground">
        No forecast data available
      </div>
    )
  }

  const path = buildPath(points)

  return (
    <div className="rounded-2xl border border-border bg-card p-4">
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        className="h-40 w-full"
        role="img"
        aria-label="Forecast rainfall chart"
      >
        <defs>
          <linearGradient id="rainfallGradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#1f6f5f" />
            <stop offset="100%" stopColor="#82c4a4" />
          </linearGradient>
        </defs>
        <path
          d={path}
          fill="none"
          stroke="url(#rainfallGradient)"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
    </div>
  )
}
