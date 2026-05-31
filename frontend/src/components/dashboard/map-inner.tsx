"use client"

import { useEffect, useMemo, useState } from "react"
import L from "leaflet"
import {
  MapContainer,
  Marker,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet"

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
})

function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap()

  useEffect(() => {
    map.setView(center, map.getZoom(), { animate: true })
  }, [center, map])

  return null
}

function ClickHandler({ onSelect }: { onSelect: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(event: L.LeafletMouseEvent) {
      onSelect(event.latlng.lat, event.latlng.lng)
    },
  })
  return null
}

export default function MapInner({
  center,
  marker,
  onSelect,
}: {
  center: [number, number]
  marker: [number, number]
  onSelect: (lat: number, lon: number) => void
}) {
  const [ready, setReady] = useState(false)
  const mapKey = useMemo(
    () => `map-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    []
  )

  useEffect(() => {
    setReady(true)
  }, [])

  if (!ready) {
    return (
      <div className="flex h-72 items-center justify-center rounded-2xl border border-dashed border-border bg-muted/40 text-sm text-muted-foreground">
        Loading map...
      </div>
    )
  }

  return (
    <MapContainer
      key={mapKey}
      center={center}
      zoom={10}
      scrollWheelZoom
      className="h-72 w-full rounded-2xl border border-border/60"
    >
      <TileLayer
        attribution="&copy; OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapUpdater center={center} />
      <ClickHandler onSelect={onSelect} />
      <Marker position={marker} />
    </MapContainer>
  )
}
