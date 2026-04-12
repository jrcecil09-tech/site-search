import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, MapPin, FileText } from 'lucide-react'
import { useProjectStore } from '@/store/projectStore'
import { SiteMap } from '@/components/map/SiteMap'
import { ResultsPanel } from '@/components/results/ResultsPanel'

export default function ProjectScreen() {
  const { id } = useParams<{ id: string }>()
  const project = useProjectStore((s) => s.projects.find((p) => p.id === id))

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <p className="text-gray-500">Project not found</p>
        <Link to="/dashboard" className="text-navy text-sm hover:underline">
          ← Back to Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-5 py-3 border-b bg-white">
        <Link to="/dashboard" className="text-gray-400 hover:text-gray-600 transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div className="flex-1">
          <h1 className="text-sm font-bold text-slate">{project.name}</h1>
          <p className="text-xs text-gray-400">{project.status} · {project.tags.join(', ') || 'no tags'}</p>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 relative">
          <SiteMap className="w-full h-full" />
          <div className="absolute bottom-4 left-4 z-10 flex gap-2">
            <button className="flex items-center gap-1.5 bg-navy text-white text-xs px-3 py-1.5 rounded-md shadow hover:bg-navy-600 transition-colors">
              <MapPin className="w-3 h-3" /> Add Site
            </button>
            <button className="flex items-center gap-1.5 bg-white border text-xs px-3 py-1.5 rounded-md shadow hover:bg-gray-50 transition-colors">
              <FileText className="w-3 h-3 text-gray-500" /> Run Queries
            </button>
          </div>
        </div>
        <div className="w-72 border-l flex-shrink-0">
          <ResultsPanel results={[]} />
        </div>
      </div>
    </div>
  )
}
