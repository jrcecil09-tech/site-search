import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type StorageBackend = 'local' | 's3' | 'azure' | 'gcs' | 'hosted'
type CoordFormat = 'decimal' | 'dms'
type Theme = 'light' | 'dark' | 'system'

interface SettingsState {
  storageBackend: StorageBackend
  coordFormat: CoordFormat
  theme: Theme
  defaultBufferMeters: number
  apiUrl: string
  setStorageBackend: (b: StorageBackend) => void
  setCoordFormat: (f: CoordFormat) => void
  setTheme: (t: Theme) => void
  setDefaultBuffer: (m: number) => void
  setApiUrl: (url: string) => void
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      storageBackend: 'local',
      coordFormat: 'decimal',
      theme: 'system',
      defaultBufferMeters: 1609,
      apiUrl: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
      setStorageBackend: (storageBackend) => set({ storageBackend }),
      setCoordFormat: (coordFormat) => set({ coordFormat }),
      setTheme: (theme) => set({ theme }),
      setDefaultBuffer: (defaultBufferMeters) => set({ defaultBufferMeters }),
      setApiUrl: (apiUrl) => set({ apiUrl }),
    }),
    { name: 'sd-settings' },
  ),
)
