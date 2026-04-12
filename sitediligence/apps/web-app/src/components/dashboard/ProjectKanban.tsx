import { ProjectCard } from './ProjectCard'
import { useProjectStore } from '@/store/projectStore'
import type { Project } from '@/store/projectStore'

const COLUMNS: { status: Project['status']; label: string; color: string }[] = [
  { status: 'draft',     label: 'Draft',     color: 'border-t-gray-300' },
  { status: 'active',    label: 'Active',    color: 'border-t-green' },
  { status: 'completed', label: 'Completed', color: 'border-t-navy' },
  { status: 'archived',  label: 'Archived',  color: 'border-t-gray-200' },
]

export function ProjectKanban() {
  const projects = useProjectStore((s) => s.projects)

  return (
    <div className="grid grid-cols-4 gap-4 h-full">
      {COLUMNS.map((col) => {
        const items = projects.filter((p) => p.status === col.status)
        return (
          <div key={col.status} className="flex flex-col">
            <div className={`border-t-2 ${col.color} bg-gray-50 rounded-t-lg p-2 mb-2`}>
              <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                {col.label}
              </span>
              <span className="ml-2 text-xs text-gray-400">{items.length}</span>
            </div>
            <div className="flex-1 space-y-2 overflow-y-auto">
              {items.map((p) => <ProjectCard key={p.id} project={p} />)}
              {items.length === 0 && (
                <div className="border-2 border-dashed rounded-lg p-4 text-center">
                  <p className="text-xs text-gray-400">No {col.label.toLowerCase()} projects</p>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
