"use client"

import SectionCard from "@/components/dashboard/section-card"

export default function SettingsPage() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
          Configuration
        </p>
        <h1 className="text-2xl font-semibold text-foreground">Settings</h1>
      </header>

      <SectionCard
        title="API Configuration"
        subtitle="Frontend environment variables"
      >
        <div className="rounded-xl border border-border/70 bg-background/80 p-4 text-sm text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>API Base URL</span>
            <span className="font-mono text-foreground">{apiBase}</span>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">
          Update <span className="font-mono">NEXT_PUBLIC_API_BASE_URL</span> in
          <span className="font-mono"> .env.local</span> to target a different
          backend.
        </p>
      </SectionCard>

      <SectionCard title="Approval Mode" subtitle="Gatekeeper behavior">
        <p className="text-sm text-muted-foreground">
          The backend uses <span className="font-mono">APPROVAL_MODE</span> to
          decide between API-driven approval or terminal input. This frontend
          expects <span className="font-mono">APPROVAL_MODE=api</span> so it can
          send approve/reject requests.
        </p>
      </SectionCard>
    </div>
  )
}
