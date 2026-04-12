import { Link, useLocation } from 'react-router-dom'
import { MapPin, LayoutDashboard, Download, Settings, Layers } from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { to: '/',          label: 'Map',       icon: MapPin },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/export',    label: 'Export',    icon: Download },
  { to: '/settings',  label: 'Settings',  icon: Settings },
] as const

export function Navbar() {
  const { pathname } = useLocation()

  return (
    <header className="h-14 bg-navy flex items-center px-5 gap-6 flex-shrink-0 shadow-md z-20">
      {/* Logo */}
      <div className="flex items-center gap-2 select-none">
        <div className="bg-green rounded-md p-1">
          <Layers className="w-4 h-4 text-white" />
        </div>
        <span className="text-white font-bold text-lg tracking-tight leading-none">
          Site<span className="text-green">Diligence</span>
        </span>
      </div>

      {/* Nav links */}
      <nav className="flex items-center gap-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-all',
              pathname === to
                ? 'bg-white/20 text-white'
                : 'text-white/60 hover:text-white hover:bg-white/10',
            )}
          >
            <Icon className="w-3.5 h-3.5" />
            {label}
          </Link>
        ))}
      </nav>

      {/* Spacer + version badge */}
      <div className="ml-auto">
        <span className="text-white/30 text-xs font-mono">v0.1.0</span>
      </div>
    </header>
  )
}
