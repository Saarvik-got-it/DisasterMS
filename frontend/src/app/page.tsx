"use client"

import { useEffect, useMemo, useState } from "react"

import ForecastChart from "@/components/dashboard/forecast-chart"
import MapPicker from "@/components/dashboard/map-picker"
import SectionCard from "@/components/dashboard/section-card"
import StatCard from "@/components/dashboard/stat-card"
import StatusPill from "@/components/dashboard/status-pill"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import {
  approveAlert,
  getMemoryRules,
  getPendingApproval,
  getRunHistory,
  rejectAlert,
  runWorkflow,
} from "@/lib/api"
import type {
  MemoryRule,
  PendingApproval,
  RunLogEntry,
  RunState,
} from "@/lib/types"

const formatValue = (value?: number, unit?: string) => {
  if (value === undefined || Number.isNaN(value)) return "n/a"
  const base = value.toFixed(2)
  return unit ? `${base} ${unit}` : base
}

const NOMINATIM_ENDPOINT =
  process.env.NEXT_PUBLIC_NOMINATIM_URL ??
  "https://nominatim.openstreetmap.org/search"

export default function Home() {
  const [locationName, setLocationName] = useState("")
  const [latitude, setLatitude] = useState(37.7749)
  const [longitude, setLongitude] = useState(-122.4194)
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<
    Array<{ display_name: string; lat: string; lon: string }>
  >([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [result, setResult] = useState<RunState | null>(null)
  const [pendingList, setPendingList] = useState<PendingApproval[]>([])
  const [activePendingId, setActivePendingId] = useState<string | null>(null)
  const [memory, setMemory] = useState<MemoryRule[]>([])
  const [runs, setRuns] = useState<RunLogEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState("")
  const [decision, setDecision] = useState<{
    status: string
    run_id: string
  } | null>(null)

  const latestWeather = useMemo(() => {
    const records = result?.weather_data ?? []
    return records[records.length - 1]
  }, [result])

  const predictionEntries = useMemo(() => {
    const prediction = result?.disaster_prediction ?? {}
    return Object.entries(prediction).filter(([key]) => key !== "most_likely")
  }, [result])

  const activePending = useMemo(() => {
    if (!pendingList.length) return null
    if (!activePendingId) return pendingList[0]
    return pendingList.find((item) => item.run_id === activePendingId) ?? pendingList[0]
  }, [pendingList, activePendingId])

  const loadMemoryAndRuns = () => {
    getMemoryRules()
      .then((data) => setMemory(data.rules ?? []))
      .catch(() => setMemory([]))

    getRunHistory()
      .then((data) => setRuns(data.runs ?? []))
      .catch(() => setRuns([]))
  }

  useEffect(() => {
    let mounted = true

    getPendingApproval()
      .then((data) => {
        if (!mounted) return
        setPendingList(data.pending ?? [])
        if (!activePendingId && data.pending?.length) {
          setActivePendingId(data.pending[0].run_id ?? null)
        }
      })
      .catch(() => setPendingList([]))

    loadMemoryAndRuns()

    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      getPendingApproval()
        .then((data) => {
          setPendingList(data.pending ?? [])
          if (!activePendingId && data.pending?.length) {
            setActivePendingId(data.pending[0].run_id ?? null)
          }
        })
        .catch(() => setPendingList([]))
    }, 4000)

    return () => clearInterval(interval)
    return () => clearInterval(interval)
  }, [activePendingId])

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }

    if (searchQuery.trim().length < 3) {
      setSearchResults([])
      return
    }

    const handle = setTimeout(() => {
      setSearchLoading(true)
      fetch(
        `${NOMINATIM_ENDPOINT}?format=json&q=${encodeURIComponent(
          searchQuery
        )}&limit=5`
      )
        .then((response) => response.json())
        .then((data) => {
          setSearchResults(Array.isArray(data) ? data : [])
        })
        .catch(() => setSearchResults([]))
        .finally(() => setSearchLoading(false))
    }, 400)

    return () => clearTimeout(handle)
  }, [searchQuery])

  const handleRun = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setDecision(null)
    setResult(null)

    try {
      const response = await runWorkflow({
        lat: latitude,
        lon: longitude,
        location_name: locationName || searchQuery || undefined,
      })
      setResult(response.state)
      setPendingList([])
      loadMemoryAndRuns()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!activePending?.run_id) {
      setError("Select a pending run before approving")
      return
    }
    try {
      const response = await approveAlert({
        run_id: activePending.run_id,
        feedback: feedback || undefined,
      })
      setDecision({ status: response.status, run_id: response.run_id })
      setFeedback("")
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleReject = async () => {
    if (!activePending?.run_id) {
      setError("Select a pending run before rejecting")
      return
    }
    try {
      const response = await rejectAlert({
        run_id: activePending.run_id,
        feedback: feedback || undefined,
      })
      setDecision({ status: response.status, run_id: response.run_id })
      setFeedback("")
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleSelectResult = (result: {
    display_name: string
    lat: string
    lon: string
  }) => {
    setLatitude(Number(result.lat))
    setLongitude(Number(result.lon))
    setLocationName(result.display_name)
    setSearchQuery(result.display_name)
    setSearchResults([])
  }

  const handleMapSelect = (lat: number, lon: number) => {
    setLatitude(lat)
    setLongitude(lon)
    if (!locationName) {
      setLocationName("Pinned location")
    }
  }

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported in this browser")
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude)
        setLongitude(position.coords.longitude)
        setLocationName("Current location")
      },
      () => setError("Unable to retrieve your location")
    )
  }

  return (
    <div className="space-y-8 stagger">
      <header className="flex flex-wrap items-center justify-between gap-6">
        <div className="fade-in">
          <p className="text-xs uppercase tracking-[0.35em] text-muted-foreground">
            Live Operations
          </p>
          <h1 className="text-3xl font-semibold text-foreground">
            Disaster Response Dashboard
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Monitor forecasts, approvals, and response readiness in one place.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {result?.severity ? <StatusPill label={result.severity} /> : null}
          {result?.routed_department ? (
            <Badge variant="secondary">{result.routed_department}</Badge>
          ) : null}
          {result?.run_id ? (
            <Badge variant="outline">Run {result.run_id.slice(0, 8)}</Badge>
          ) : null}
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <SectionCard
          title="Location & Controls"
          subtitle="Trigger the workflow and monitor approval status"
        >
          <form onSubmit={handleRun} className="grid gap-4">
            <div className="grid gap-4">
              <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
                <div className="space-y-2">
                  <Input
                    placeholder="Search a city, region, or landmark"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                  />
                  {searchLoading ? (
                    <p className="text-xs text-muted-foreground">Searching...</p>
                  ) : searchResults.length ? (
                    <div className="rounded-xl border border-border/70 bg-background/90 p-2 text-sm">
                      {searchResults.map((result) => (
                        <button
                          key={`${result.display_name}-${result.lat}`}
                          type="button"
                          className="block w-full rounded-lg px-2 py-2 text-left text-muted-foreground hover:bg-muted"
                          onClick={() => handleSelectResult(result)}
                        >
                          {result.display_name}
                        </button>
                      ))}
                    </div>
                  ) : null}
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                    <span>Selected: {locationName || "None"}</span>
                    <span>
                      {latitude.toFixed(4)}, {longitude.toFixed(4)}
                    </span>
                  </div>
                </div>
                <div className="flex items-start">
                  <Button type="button" variant="outline" onClick={handleUseMyLocation}>
                    Use My Location
                  </Button>
                </div>
              </div>
              <MapPicker
                latitude={latitude}
                longitude={longitude}
                onSelect={handleMapSelect}
              />
            </div>
            <div className="flex flex-wrap gap-3">
              <Button type="submit" disabled={loading}>
                {loading ? "Running workflow..." : "Run workflow"}
              </Button>
              {pendingList.length ? (
                <Badge variant="outline">
                  Awaiting approval ({pendingList.length})
                </Badge>
              ) : null}
              {decision ? (
                <Badge variant="secondary">
                  Decision: {decision.status} ({decision.run_id.slice(0, 8)})
                </Badge>
              ) : null}
            </div>
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
          </form>

          <Separator />

          <div className="grid gap-4">
            {pendingList.length ? (
              <div className="rounded-xl border border-border/70 bg-background/80 p-3 text-sm">
                <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                  Pending Approvals
                </p>
                <div className="mt-3 space-y-2">
                  {pendingList.map((item) => (
                    <button
                      key={item.run_id}
                      type="button"
                      className={`w-full rounded-lg border px-3 py-2 text-left text-xs transition-colors ${
                        item.run_id === activePending?.run_id
                          ? "border-primary/60 bg-primary/10 text-foreground"
                          : "border-border/60 bg-muted/20 text-muted-foreground hover:bg-muted"
                      }`}
                      onClick={() => setActivePendingId(item.run_id ?? null)}
                    >
                      <div className="flex items-center justify-between">
                        <span>{item.routed_department ?? "Pending"}</span>
                        <span className="font-mono">
                          {(item.run_id ?? "").slice(0, 8)}
                        </span>
                      </div>
                      <div className="mt-1 text-[0.7rem] text-muted-foreground">
                        Severity: {item.severity ?? "n/a"}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No pending approvals right now.
              </p>
            )}
            <Textarea
              placeholder="Feedback for approval or rejection"
              value={feedback}
              onChange={(event) => setFeedback(event.target.value)}
              rows={3}
            />
            <div className="flex flex-wrap gap-3">
              <Button onClick={handleApprove} disabled={!activePending?.run_id}>
                Approve
              </Button>
              <Button
                variant="destructive"
                onClick={handleReject}
                disabled={!activePending?.run_id}
              >
                Reject
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Approvals are sent to the backend gatekeeper. If a workflow is
              waiting, approve/reject to continue.
            </p>
          </div>
        </SectionCard>

        <SectionCard
          title="Live Situation"
          subtitle="Current weather snapshot and routing outcome"
        >
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard
              title="Temperature"
              value={formatValue(latestWeather?.temperature, "°C")}
              description="Latest observed reading"
            />
            <StatCard
              title="Humidity"
              value={formatValue(latestWeather?.humidity, "%")}
              description="Relative humidity"
            />
            <StatCard
              title="Rainfall"
              value={formatValue(latestWeather?.rainfall, "mm")}
              description="Recent precipitation"
            />
            <StatCard
              title="Wind Speed"
              value={formatValue(latestWeather?.wind_speed, "m/s")}
              description="Surface winds"
            />
            <StatCard
              title="Pressure"
              value={formatValue(latestWeather?.pressure, "hPa")}
              description="Mean sea level"
            />
          </div>

          <Separator />

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                Routed Department
              </p>
              <p className="text-lg font-semibold text-foreground">
                {result?.routed_department ?? "Awaiting"}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                Severity
              </p>
              <p className="text-lg font-semibold text-foreground">
                {result?.severity ?? "Pending"}
              </p>
            </div>
          </div>
          {result?.severity_reason ? (
            <p className="text-sm text-muted-foreground">
              {result.severity_reason}
            </p>
          ) : null}
        </SectionCard>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <SectionCard
          title="Forecast"
          subtitle="48-hour rainfall projection"
        >
          <ForecastChart points={result?.forecast?.points ?? []} />
          <div className="grid gap-4 sm:grid-cols-2">
            <StatCard
              title="Predicted Rainfall"
              value={formatValue(result?.forecast?.features?.predicted_rainfall, "mm")}
              description="Average predicted rainfall"
            />
            <StatCard
              title="Temperature Trend"
              value={formatValue(result?.forecast?.features?.temperature_trend, "°C")}
              description="24-hour change"
            />
          </div>
        </SectionCard>

        <SectionCard title="Disaster Probabilities" subtitle="Classifier output">
          {predictionEntries.length ? (
            <div className="space-y-3">
              {predictionEntries.map(([label, value]) => {
                const numeric = typeof value === "number" ? value : 0
                return (
                  <div key={label} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-semibold text-foreground">{label}</span>
                      <span className="text-muted-foreground">
                        {(numeric * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${Math.min(numeric * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No classifier output available yet.
            </p>
          )}
          {result?.disaster_prediction?.most_likely ? (
            <p className="text-sm text-muted-foreground">
              Most likely: {result.disaster_prediction.most_likely}
            </p>
          ) : null}
        </SectionCard>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <SectionCard
          title="Alert & Action Plan"
          subtitle="Generated output awaiting approval"
        >
          {activePending?.run_id ? (
            <p className="text-xs text-muted-foreground">
              Run ID: {activePending.run_id}
            </p>
          ) : null}
          <div className="rounded-xl border border-border/70 bg-background/80 p-4 text-sm text-foreground">
            {activePending?.generated_alert || result?.generated_alert ||
            "No alert generated yet."}
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
              Action Plan
            </p>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              {(activePending?.action_plan ?? result?.action_plan ?? []).length ? (
                (activePending?.action_plan ?? result?.action_plan ?? []).map(
                  (item, index) => (
                    <li key={`${item}-${index}`} className="flex gap-2">
                      <span className="text-primary">●</span>
                      <span>{item}</span>
                    </li>
                  )
                )
              ) : (
                <li>No action plan available.</li>
              )}
            </ul>
          </div>
        </SectionCard>

        <SectionCard title="News Context" subtitle="Headlines informing severity">
          {(result?.news_context ?? []).length ? (
            <ScrollArea className="h-64 pr-3">
              <ul className="space-y-3 text-sm text-muted-foreground">
                {result?.news_context?.map((headline, index) => (
                  <li key={`${headline}-${index}`}>{headline}</li>
                ))}
              </ul>
            </ScrollArea>
          ) : (
            <p className="text-sm text-muted-foreground">
              No headlines available yet.
            </p>
          )}
        </SectionCard>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <SectionCard
          title="Persistent Memory"
          subtitle="Human feedback captured across runs"
        >
          {memory.length ? (
            <ScrollArea className="h-64 pr-3">
              <div className="space-y-3">
                {memory
                  .slice()
                  .reverse()
                  .map((rule) => (
                    <div
                      key={`${rule.timestamp}-${rule.rule}`}
                      className="rounded-xl border border-border/70 bg-background/80 p-3 text-sm"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-foreground">
                          {rule.department}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(rule.timestamp).toLocaleString()}
                        </span>
                      </div>
                      {rule.run_id ? (
                        <p className="mt-1 text-xs text-muted-foreground">
                          Run ID: {rule.run_id.slice(0, 8)}
                        </p>
                      ) : null}
                      <p className="mt-2 text-muted-foreground">{rule.rule}</p>
                    </div>
                  ))}
              </div>
            </ScrollArea>
          ) : (
            <p className="text-sm text-muted-foreground">
              No persistent rules stored yet.
            </p>
          )}
        </SectionCard>

        <SectionCard
          title="Previous Runs"
          subtitle="Latest workflow outcomes"
        >
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : runs.length ? (
            <ScrollArea className="h-64 pr-3">
              <div className="space-y-3 text-sm">
                {runs
                  .slice()
                  .reverse()
                  .slice(0, 5)
                  .map((run) => (
                    <div
                      key={run.timestamp}
                      className="rounded-xl border border-border/70 bg-background/80 p-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-foreground">
                          {run.location_name ?? run.location ?? "Unknown location"}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(run.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
                        <span>Run: {run.run_id?.slice(0, 8) ?? "n/a"}</span>
                        <span>Severity: {run.severity ?? "n/a"}</span>
                        <span>Dept: {run.routed_department ?? "n/a"}</span>
                        <span>Status: {run.approval_status ?? "n/a"}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </ScrollArea>
          ) : (
            <p className="text-sm text-muted-foreground">No runs logged yet.</p>
          )}
        </SectionCard>
      </section>
    </div>
  )
}
