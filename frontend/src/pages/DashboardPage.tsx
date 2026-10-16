import { useQuery } from '@tantml:parameter name="query"'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { data: stats } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get('/dashboard/stats')).data
  })

  const logout = () => {
    localStorage.clear()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-blue-900 text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-xl font-bold">ReadmitCare</h1>
          <div className="space-x-4">
            <button onClick={() => navigate('/')} className="hover:underline">Dashboard</button>
            <button onClick={() => navigate('/patients')} className="hover:underline">Patients</button>
            <button onClick={logout} className="hover:underline">Logout</button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto p-8">
        <h2 className="text-3xl font-bold mb-6">Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-gray-600 text-sm">Total Patients</div>
            <div className="text-3xl font-bold">{stats?.total_patients || 0}</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-gray-600 text-sm">Active Encounters</div>
            <div className="text-3xl font-bold">{stats?.active_encounters || 0}</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-gray-600 text-sm">High Risk Count</div>
            <div className="text-3xl font-bold text-red-600">{stats?.high_risk_count || 0}</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-gray-600 text-sm">Avg Risk Score</div>
            <div className="text-3xl font-bold">{stats?.avg_risk_score || 0}%</div>
          </div>
        </div>
      </div>
    </div>
  )
}
