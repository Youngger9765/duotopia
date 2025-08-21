import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, Users } from 'lucide-react'
import { api } from '@/lib/api'

export default function InstitutionalClassrooms() {
  const [classrooms, setClassrooms] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchClassrooms()
  }, [])

  const fetchClassrooms = async () => {
    try {
      const response = await api.get('/api/institutional/classrooms')
      setClassrooms(response.data)
    } catch (error) {
      console.error('Failed to fetch classrooms:', error)
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
        <h1 className="text-2xl font-bold">教室管理</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          新增教室
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {classrooms.map((classroom: any) => (
          <Card key={classroom.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                {classroom.name}
                <span className="text-sm font-normal text-gray-500">
                  <Users className="inline h-4 w-4 mr-1" />
                  {classroom.student_count || 0}/{classroom.capacity || 30}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">年級: {classroom.grade_level}</p>
              <p className="text-sm text-gray-600">教室號: {classroom.room_number}</p>
              <p className="text-sm text-gray-600">學校: {classroom.school_name}</p>
              <div className="mt-4 flex justify-end space-x-2">
                <Button size="sm" variant="outline">編輯</Button>
                <Button size="sm" variant="outline">檢視學生</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}