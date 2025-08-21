import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, BookOpen } from 'lucide-react'
import { api } from '@/lib/api'

export default function InstitutionalCourses() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCourses()
  }, [])

  const fetchCourses = async () => {
    try {
      const response = await api.get('/api/institutional/courses')
      setCourses(response.data)
    } catch (error) {
      console.error('Failed to fetch courses:', error)
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
        <h1 className="text-2xl font-bold">課程管理</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          新增課程
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {courses.map((course: any) => (
          <Card key={course.id}>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BookOpen className="mr-2 h-5 w-5" />
                {course.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-2">{course.description}</p>
              <p className="text-sm text-gray-500">難度: {course.difficulty_level}</p>
              <p className="text-sm text-gray-500">學校: {course.school_name}</p>
              <p className="text-sm text-gray-500">課時數: {course.lesson_count || 0}</p>
              <div className="mt-4 flex justify-end space-x-2">
                <Button size="sm" variant="outline">編輯</Button>
                <Button size="sm" variant="outline">檢視課時</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}