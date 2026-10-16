import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'

export default function PatientDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  
  const { data: patient } = useQuery({
    queryKey: ['patient', id],
    queryFn: async () => (await api.get(`/patients/${id}`)).data
  })

  if (!patient) return <div>Loading...</div>

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
        <button onClick={() => navigate('/patients')} className="mb-4 text-blue-600 hover:underline">
          ← Back to Patients
        </button>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold mb-4">Patient Details</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-gray-600 text-sm">MRN</label>
              <div className="font-medium">{patient.mrn}</div>
            </div>
            <div>
              <label className="text-gray-600 text-sm">Name</label>
              <div className="font-medium">{patient.first_name} {patient.last_name}</div>
            </div>
            <div>
              <label className="text-gray-600 text-sm">Date of Birth</label>
              <div className="font-medium">{patient.date_of_birth}</div>
            </div>
            <div>
              <label className="text-gray-600 text-sm">Gender</label>
              <div className="font-medium">{patient.gender}</div>
            </div>
            {patient.phone && (
              <div>
                <label className="text-gray-600 text-sm">Phone</label>
                <div className="font-medium">{patient.phone}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
