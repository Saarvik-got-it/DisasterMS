"use client"

import { useEffect, useState } from "react"

import SectionCard from "@/components/dashboard/section-card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { getRunHistory } from "@/lib/api"
import type { RunLogEntry } from "@/lib/types"

export default function HistoryPage() {
  const [runs, setRuns] = useState<RunLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    getRunHistory()
      .then((data) => {
        if (!mounted) return
        setRuns(data.runs ?? [])
        setError(null)
      })
      .catch((err: Error) => {
        if (!mounted) return
        setError(err.message)
      })
      .finally(() => {
        if (!mounted) return
        setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            Operations Log
          </p>
          <h1 className="text-2xl font-semibold text-foreground">
            Previous Runs
          </h1>
        </div>
      </header>

      <SectionCard
        title="Run History"
        subtitle="Recent workflow executions captured by the backend"
      >
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : error ? (
          <p className="text-sm text-destructive">{error}</p>
        ) : runs.length ? (
          <ScrollArea className="h-96 pr-3">
            <div className="space-y-4">
              {runs
                .slice()
                .reverse()
                .map((run) => (
                  <div
                    key={run.timestamp}
                    className="rounded-xl border border-border/70 bg-background/80 p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-foreground">
                        {run.location_name ?? run.location ?? "Unknown location"}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(run.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="mt-2 grid gap-2 text-sm text-muted-foreground sm:grid-cols-3">
                      <div>Run ID: {run.run_id?.slice(0, 8) ?? "n/a"}</div>
                      <div>
                        Coords: {run.latitude?.toFixed(4) ?? "n/a"}, {run.longitude?.toFixed(4) ?? "n/a"}
                      </div>
                      <div>Severity: {run.severity ?? "n/a"}</div>
                      <div>Department: {run.routed_department ?? "n/a"}</div>
                      <div>Status: {run.approval_status ?? "n/a"}</div>
                      <div>Hazard: {run.most_likely ?? "n/a"}</div>
                    </div>
                  </div>
                ))}
            </div>
          </ScrollArea>
        ) : (
          <p className="text-sm text-muted-foreground">No runs logged yet.</p>
        )}
      </SectionCard>
    </div>
  )
}
