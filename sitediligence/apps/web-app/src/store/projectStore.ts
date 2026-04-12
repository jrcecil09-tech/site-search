import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Project {
  id: string
  name: string
  description: string
  status: 'draft' | 'active' | 'completed' | 'archived'
  createdAt: string
  tags: string[]
}

interface ProjectState {
  projects: Project[]
  activeProjectId: string | null
  setActiveProject: (id: string | null) => void
  addProject: (project: Project) => void
  updateProject: (id: string, patch: Partial<Project>) => void
  removeProject: (id: string) => void
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set) => ({
      projects: [],
      activeProjectId: null,
      setActiveProject: (id) => set({ activeProjectId: id }),
      addProject: (project) =>
        set((s) => ({ projects: [...s.projects, project] })),
      updateProject: (id, patch) =>
        set((s) => ({
          projects: s.projects.map((p) => (p.id === id ? { ...p, ...patch } : p)),
        })),
      removeProject: (id) =>
        set((s) => ({ projects: s.projects.filter((p) => p.id !== id) })),
    }),
    { name: 'sd-projects' },
  ),
)
