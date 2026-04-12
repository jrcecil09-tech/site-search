import { StorageSettings } from '@/components/storage/StorageSettings'
import { SyncStatus } from '@/components/storage/SyncStatus'
import { useSettingsStore } from '@/store/settingsStore'
import { Settings } from 'lucide-react'

export default function SettingsScreen() {
  const { apiUrl, setApiUrl, defaultBufferMeters, setDefaultBuffer, coordFormat, setCoordFormat } =
    useSettingsStore()

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-8">
      <div className="flex items-center gap-2">
        <Settings className="w-5 h-5 text-navy" />
        <h1 className="text-lg font-bold text-slate">Settings</h1>
      </div>

      {/* API */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-slate border-b pb-2">API Connection</h2>
        <label className="block">
          <span className="text-xs text-gray-500 uppercase tracking-wide">Backend URL</span>
          <input
            type="url"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            className="mt-1 w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-navy font-mono"
          />
        </label>
        <SyncStatus />
      </section>

      {/* Map */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-slate border-b pb-2">Map & Coordinates</h2>
        <label className="block">
          <span className="text-xs text-gray-500 uppercase tracking-wide">Default Buffer (meters)</span>
          <input
            type="number"
            value={defaultBufferMeters}
            onChange={(e) => setDefaultBuffer(Number(e.target.value))}
            min={100}
            max={50000}
            step={100}
            className="mt-1 w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-navy"
          />
          <p className="text-xs text-gray-400 mt-1">1609 m = 1 mile</p>
        </label>
        <label className="block">
          <span className="text-xs text-gray-500 uppercase tracking-wide">Coordinate Format</span>
          <select
            value={coordFormat}
            onChange={(e) => setCoordFormat(e.target.value as 'decimal' | 'dms')}
            className="mt-1 w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-navy"
          >
            <option value="decimal">Decimal Degrees (38.8977, -77.0366)</option>
            <option value="dms">DMS (38°53′52″N, 77°02′11″W)</option>
          </select>
        </label>
      </section>

      {/* Storage */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-slate border-b pb-2">File Storage</h2>
        <StorageSettings />
      </section>
    </div>
  )
}
