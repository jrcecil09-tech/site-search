export function Footer() {
  return (
    <footer className="h-8 bg-slate/90 flex items-center justify-between px-4 flex-shrink-0">
      <span className="text-white/30 text-xs">
        SiteDiligence © {new Date().getFullYear()}
      </span>
      <span className="text-white/20 text-xs font-mono">
        api: {import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}
      </span>
    </footer>
  )
}
