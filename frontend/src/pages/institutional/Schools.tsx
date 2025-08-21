import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import { api } from '@/lib/api'

export default function InstitutionalSchools() {
  const [schools, setSchools] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSchools()
  }, [])

  const fetchSchools = async () => {
    try {
      const response = await api.get('/api/institutional/schools')
      setSchools(response.data)
    } catch (error) {
      console.error('Failed to fetch schools:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div>載入中...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">學校管理</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          新增學校
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {schools.map((school: any) => (
          <Card key={school.id}>
            <CardHeader>
              <CardTitle>{school.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">代碼: {school.code}</p>
              <p className="text-sm text-gray-600">地址: {school.address}</p>
              <div className="mt-4 flex justify-end space-x-2">
                <Button size="sm" variant="outline">編輯</Button>
                <Button size="sm" variant="outline">檢視</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}