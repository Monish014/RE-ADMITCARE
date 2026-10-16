import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import api from '../api/client'

export default function PatientsPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  
  const { data } = useQuery({
    queryKey: ['patients', page, search],
    queryFn: async () => (await api.get(`/patients?page=${page}&search=${search}`)).data
  })

  const getRiskColor = (band: string) => {
    if (band === 'high') return 'text-red-600 bg-red-100'
    if (band === 'medium') return 'text-yellow-600 bg-yellow-100'
    return 'text-green-600 bg-green-100'
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-blue-900 text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-xl font-bold">ReadmitCare</h1>
          <div className="space-x-4">
            <button onClick={() => navigate('/')} className="hover:underline">Dashboard</button>
            <button onClick={() => navigate('/patients')} className="hover:underline">Patients</button>
            <button onClick={() => { localStorage.clear(); navigate('/login') }} className="hover:underline">Logout</button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto p-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold">Patients</h2>
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-4 py-2 border rounded"
          />
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">MRN</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">DOB</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data?.items?.map((p: any) => (
                <tr key={p.id} onClick={() => navigate(`/patients/${p.id}`)} className="hover:bg-gray-50 cursor-pointer">
                  <td className="px-6 py-4">{p.mrn}</td>
                  <td className="px-6 py-4">{p.first_name} {p.last_name}</td>
                  <td className="px-6 py-4">{p.date_of_birth}</td>
                  <td className="px-6 py-4">
                    {p.risk_band && (
                      <span className={`px-2 py-1 rounded ${getRiskColor(p.risk_band)}`}>
                        {p.risk_band} ({p.current_risk_score?.toFixed(1)}%)
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex justify-between">
          <button 
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 bg-blue-600 text-white rounded disabled:bg-gray-300"
          >
            Previous
          </button>
          <span>Page {page} of {Math.ceil((data?.total || 0) / 20)}</span>
          <button 
            onClick={() => setPage(p => p + 1)}
            disabled={page >= Math.ceil((data?.total || 0) / 20)}
            className="px-4 py-2 bg-blue-600 text-white rounded disabled:bg-gray-300"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
