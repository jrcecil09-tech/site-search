import { useSettingsStore } from '@/store/settingsStore'
import { HardDrive } from 'lucide-react'

const BACKENDS = [
  { value: 'local',   label: 'Local Filesystem' },
  { value: 's3',      label: 'Amazon S3 / R2' },
  { value: 'azure',   label: 'Azure Blob Storage' },
  { value: 'gcs',     label: 'Google Cloud Storage' },
  { value: 'hosted',  label: 'SiteDiligence Hosted' },
] as const

export function StorageSettings() {
  const { storageBackend, setStorageBackend } = useSettingsStore()

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <HardDrive className="w-4 h-4 text-navy" />
        <span className="text-sm font-semibold text-slate">Storage Backend</span>
      </div>
      <div className="space-y-2">
        {BACKENDS.map((b) => (
          <label key={b.value} className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
            <input
              type="radio"
              name="storage-backend"
              value={b.value}
              checked={storageBackend === b.value}
              onChange={() => setStorageBackend(b.value)}
              className="accent-navy"
            />
            <div>
              <p className="text-sm font-medium text-slate">{b.label}</p>
              <p className="text-xs text-gray-400">{b.value}</p>
            </div>
          </label>
        ))}
      </div>
    </div>
  )
}
