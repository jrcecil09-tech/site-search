import { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'

interface AddressResult {
  display_name: string
  lat: string
  lon: string
}

interface AddressSearchProps {
  onSelect: (lat: number, lng: number, address: string) => void
}

export function AddressSearch({ onSelect }: AddressSearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<AddressResult[]>([])
  const [loading, setLoading] = useState(false)

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      // Use Nominatim for address geocoding (free, no key required)
      const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=5&countrycodes=us`
      const res = await fetch(url, { headers: { 'Accept-Language': 'en' } })
      const data = await res.json()
      setResults(data)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold text-slate uppercase tracking-wide">
        Address Search
      </label>
      <div className="flex gap-1.5">
        <input
          type="text"
          placeholder="Enter address or place name…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
          className="flex-1 px-3 py-1.5 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-navy"
        />
        <button
          onClick={search}
          disabled={loading}
          className="px-3 py-1.5 bg-navy text-white rounded-md hover:bg-navy-600 transition-colors disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
        </button>
      </div>
      {results.length > 0 && (
        <ul className="border rounded-md divide-y text-sm">
          {results.map((r, i) => (
            <li key={i}>
              <button
                onClick={() => {
                  onSelect(parseFloat(r.lat), parseFloat(r.lon), r.display_name)
                  setResults([])
                  setQuery(r.display_name)
                }}
                className="w-full text-left px-3 py-2 hover:bg-gray-50 text-xs leading-snug"
              >
                {r.display_name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
