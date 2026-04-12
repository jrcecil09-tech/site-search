import { NavLink } from 'react-router-dom'
import { MapPin, FolderOpen, FileText, HardDrive, BarChart2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useProjectStore } from '@/store/projectStore'

const LINKS = [
  { to: '/',          icon: MapPin,    label: 'Site Map' },
  { to: '/dashboard', icon: FolderOpen,label: 'Projects' },
  { to: '/export',    icon: FileText,  label: 'Export' },
  { to: '/settings',  icon: HardDrive, label: 'Storage' },
] as const

export function Sidebar() {
  const projects = useProjectStore((s) => s.projects)

  return (
    <aside className="w-14 bg-slate flex flex-col items-center py-3 gap-2 flex-shrink-0 z-10">
      {LINKS.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          title={label}
          className={({ isActive }) =>
            cn(
              'w-9 h-9 flex items-center justify-center rounded-lg transition-all',
              isActive
                ? 'bg-navy text-white'
                : 'text-white/40 hover:text-white hover:bg-white/10',
            )
          }
        >
          <Icon className="w-4 h-4" />
        </NavLink>
      ))}

      <div className="mt-auto flex flex-col items-center gap-1">
        {projects.length > 0 && (
          <div className="w-5 h-5 rounded-full bg-green flex items-center justify-center">
            <span className="text-white text-[9px] font-bold">{projects.length}</span>
          </div>
        )}
        <BarChart2 className="w-4 h-4 text-white/20" />
      </div>
    </aside>
  )
}
