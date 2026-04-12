import { useState } from 'react'
import { MapPin } from 'lucide-react'

interface CoordinateInputProps {
  onSubmit: (lat: number, lng: number) => void
}

export function CoordinateInput({ onSubmit }: CoordinateInputProps) {
  const [lat, setLat] = useState('')
  const [lng, setLng] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const parsedLat = parseFloat(lat)
    const parsedLng = parseFloat(lng)
    if (isNaN(parsedLat) || parsedLat < -90 || parsedLat > 90) {
      setError('Latitude must be between -90 and 90')
      return
    }
    if (isNaN(parsedLng) || parsedLng < -180 || parsedLng > 180) {
      setError('Longitude must be between -180 and 180')
      return
    }
    setError('')
    onSubmit(parsedLat, parsedLng)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <label className="block text-xs font-semibold text-slate uppercase tracking-wide">
        Coordinates
      </label>
      <div className="space-y-2">
        <input
          type="number"
          step="any"
          placeholder="Latitude (e.g. 38.8977)"
          value={lat}
          onChange={(e) => setLat(e.target.value)}
          className="w-full px-3 py-1.5 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-navy"
        />
        <input
          type="number"
          step="any"
          placeholder="Longitude (e.g. -77.0366)"
          value={lng}
          onChange={(e) => setLng(e.target.value)}
          className="w-full px-3 py-1.5 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-navy"
        />
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
      <button
        type="submit"
        className="w-full flex items-center justify-center gap-2 bg-navy text-white text-sm py-1.5 rounded-md hover:bg-navy-600 transition-colors"
      >
        <MapPin className="w-3.5 h-3.5" />
        Go to Location
      </button>
    </form>
  )
}
