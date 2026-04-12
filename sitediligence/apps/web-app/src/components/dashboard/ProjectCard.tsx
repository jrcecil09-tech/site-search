import { format } from 'date-fns'
import { FolderOpen, MapPin, Tag } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'
import type { Project } from '@/store/projectStore'

const STATUS_COLORS: Record<Project['status'], string> = {
  draft:     'bg-gray-100 text-gray-600',
  active:    'bg-green/10 text-green-700',
  completed: 'bg-navy/10 text-navy',
  archived:  'bg-gray-100 text-gray-400',
}

interface ProjectCardProps {
  project: Project
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link
      to={`/projects/${project.id}`}
      className="block bg-white border rounded-lg p-4 hover:shadow-md hover:border-navy/30 transition-all"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <FolderOpen className="w-4 h-4 text-navy flex-shrink-0" />
          <span className="font-medium text-slate text-sm leading-tight">{project.name}</span>
        </div>
        <span className={cn('text-[10px] px-1.5 py-0.5 rounded font-medium flex-shrink-0', STATUS_COLORS[project.status])}>
          {project.status}
        </span>
      </div>

      {project.description && (
        <p className="mt-2 text-xs text-gray-500 line-clamp-2">{project.description}</p>
      )}

      <div className="mt-3 flex items-center gap-3 text-[10px] text-gray-400">
        <span className="flex items-center gap-1">
          <MapPin className="w-3 h-3" /> 0 sites
        </span>
        <span className="flex items-center gap-1">
          <Tag className="w-3 h-3" /> {project.tags.length} tags
        </span>
        <span className="ml-auto">
          {format(new Date(project.createdAt), 'MMM d, yyyy')}
        </span>
      </div>
    </Link>
  )
}
