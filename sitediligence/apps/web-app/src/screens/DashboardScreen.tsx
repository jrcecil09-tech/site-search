import { useState } from 'react'
import { Plus, LayoutGrid, Columns } from 'lucide-react'
import { ProjectCard } from '@/components/dashboard/ProjectCard'
import { ProjectKanban } from '@/components/dashboard/ProjectKanban'
import { useProjectStore } from '@/store/projectStore'
import { cn } from '@/lib/utils'

type View = 'grid' | 'kanban'

export default function DashboardScreen() {
  const [view, setView] = useState<View>('grid')
  const projects = useProjectStore((s) => s.projects)
  const addProject = useProjectStore((s) => s.addProject)

  const createDemo = () => {
    addProject({
      id: crypto.randomUUID(),
      name: `Demo Project ${projects.length + 1}`,
      description: 'Sample site diligence project',
      status: 'active',
      createdAt: new Date().toISOString(),
      tags: ['demo'],
    })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b bg-white">
        <div>
          <h1 className="text-lg font-bold text-slate">Projects</h1>
          <p className="text-xs text-gray-500">{projects.length} project{projects.length !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex border rounded-md overflow-hidden">
            {([['grid', LayoutGrid], ['kanban', Columns]] as [View, typeof LayoutGrid][]).map(([v, Icon]) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={cn(
                  'px-2.5 py-1.5 transition-colors',
                  view === v ? 'bg-navy text-white' : 'text-gray-500 hover:bg-gray-50',
                )}
              >
                <Icon className="w-3.5 h-3.5" />
              </button>
            ))}
          </div>
          <button
            onClick={createDemo}
            className="flex items-center gap-1.5 bg-navy text-white text-sm px-3 py-1.5 rounded-md hover:bg-navy-600 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            New Project
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 gap-3 text-gray-400">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
              <Plus className="w-8 h-8" />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-gray-600">No projects yet</p>
              <p className="text-xs mt-1">Click "New Project" to get started</p>
            </div>
          </div>
        ) : view === 'grid' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((p) => <ProjectCard key={p.id} project={p} />)}
          </div>
        ) : (
          <ProjectKanban />
        )}
      </div>
    </div>
  )
}
