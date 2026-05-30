import type { Metadata } from "next"
import { IBM_Plex_Mono, Space_Grotesk } from "next/font/google"

import TopNav from "@/components/layout/top-nav"
import "leaflet/dist/leaflet.css"
import "./globals.css"

const spaceGrotesk = Space_Grotesk({
  variable: "--font-ops-sans",
  subsets: ["latin"],
})

const plexMono = IBM_Plex_Mono({
  variable: "--font-ops-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
})

export const metadata: Metadata = {
  title: "Disaster Operations Console",
  description: "Autonomous Disaster Management System dashboard",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${plexMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full bg-background text-foreground" suppressHydrationWarning>
        <div className="relative flex min-h-screen flex-col">
          <div className="pointer-events-none absolute inset-0 bg-ops-grid" />
          <header className="relative z-10 border-b border-border/60 bg-background/80 backdrop-blur">
            <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
              <div>
                <p className="text-xs uppercase tracking-[0.4em] text-muted-foreground">
                  Operations Console
                </p>
                <h1 className="text-lg font-semibold text-foreground">
                  Disaster Management
                </h1>
              </div>
              <TopNav />
            </div>
          </header>
          <main className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 flex-col px-6 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
