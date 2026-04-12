import { CheckCircle, RefreshCw, WifiOff } from 'lucide-react'
import { useSettingsStore } from '@/store/settingsStore'

export function SyncStatus() {
  const backend = useSettingsStore((s) => s.storageBackend)

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-white border rounded-lg">
      {backend === 'local' ? (
        <>
          <CheckCircle className="w-3.5 h-3.5 text-green" />
          <span className="text-xs text-gray-600">Local storage — always available</span>
        </>
      ) : (
        <>
          <RefreshCw className="w-3.5 h-3.5 text-amber animate-spin" />
          <span className="text-xs text-gray-600">Syncing with {backend}…</span>
        </>
      )}
      <WifiOff className="w-3 h-3 text-gray-300 ml-auto" title="Offline mode available" />
    </div>
  )
}
