import { useState, useCallback } from 'react'
import { useMapStore } from '@/store/mapStore'

export interface BoundaryState {
  coords: [number, number] | null
  bbox: [number, number, number, number] | null
  bufferMeters: number
}

export function useBoundary(defaultBuffer = 1609) {
  const setSelectedCoords = useMapStore((s) => s.setSelectedCoords)
  const setCenter = useMapStore((s) => s.setCenter)

  const [state, setState] = useState<BoundaryState>({
    coords: null,
    bbox: null,
    bufferMeters: defaultBuffer,
  })

  const setCoords = useCallback(
    (lat: number, lng: number) => {
      const coords: [number, number] = [lng, lat] // GeoJSON order [lon, lat]
      const buf = state.bufferMeters / 111_320 // approx degrees
      const bbox: [number, number, number, number] = [
        lng - buf, lat - buf, lng + buf, lat + buf,
      ]
      setState((s) => ({ ...s, coords, bbox }))
      setSelectedCoords(coords)
      setCenter([lat, lng])
    },
    [state.bufferMeters, setSelectedCoords, setCenter],
  )

  const setBuffer = useCallback((meters: number) => {
    setState((s) => ({ ...s, bufferMeters: meters }))
  }, [])

  const clear = useCallback(() => {
    setState({ coords: null, bbox: null, bufferMeters: defaultBuffer })
    setSelectedCoords(null)
  }, [defaultBuffer, setSelectedCoords])

  return { ...state, setCoords, setBuffer, clear }
}
