"use client"

import dynamic from "next/dynamic"

const MapInner = dynamic(() => import("@/components/dashboard/map-inner"), {
  ssr: false,
})

export default function MapPicker({
  latitude,
  longitude,
  onSelect,
}: {
  latitude: number
  longitude: number
  onSelect: (lat: number, lon: number) => void
}) {
  const center: [number, number] = [latitude, longitude]

  return <MapInner center={center} marker={center} onSelect={onSelect} />
}
