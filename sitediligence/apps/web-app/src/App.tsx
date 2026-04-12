import { Routes, Route } from 'react-router-dom'
import { Navbar } from '@/components/layout/Navbar'
import { Sidebar } from '@/components/layout/Sidebar'
import HomeScreen from '@/screens/HomeScreen'
import DashboardScreen from '@/screens/DashboardScreen'
import ProjectScreen from '@/screens/ProjectScreen'
import SettingsScreen from '@/screens/SettingsScreen'
import ExportScreen from '@/screens/ExportScreen'

export default function App() {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-gray-50">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<HomeScreen />} />
            <Route path="/dashboard" element={<DashboardScreen />} />
            <Route path="/projects/:id" element={<ProjectScreen />} />
            <Route path="/settings" element={<SettingsScreen />} />
            <Route path="/export" element={<ExportScreen />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
