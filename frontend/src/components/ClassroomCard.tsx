import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Edit, Trash2 } from 'lucide-react'
import type { Class } from '@/types'

interface ClassroomCardProps {
  classroom: Class
  studentCount: number
  onEdit: (classroom: Class) => void
  onDelete: (classroom: Class) => void
  isLoading?: boolean
}

export const ClassroomCard: React.FC<ClassroomCardProps> = ({
  classroom,
  studentCount,
  onEdit,
  onDelete,
  isLoading,
}) => {
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div data-testid="classroom-card-skeleton">
        <Card className="animate-pulse">
          <CardHeader>
            <div className="h-6 bg-gray-200 rounded w-3/4"></div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const isFull = studentCount >= classroom.capacity

  return (
    <Card role="article">
      <CardHeader>
        <CardTitle>{classroom.name}</CardTitle>
        <p className="text-sm text-gray-500">{classroom.grade}</p>
      </CardHeader>
      <CardContent>
        <p className="text-gray-600 mb-4">
          {classroom.description || '暫無描述'}
        </p>
        
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">學生人數</span>
            <span
              className={`px-2 py-1 rounded-full text-xs font-medium ${
                isFull
                  ? 'bg-red-100 text-red-800'
                  : 'bg-blue-100 text-blue-800'
              }`}
            >
              {studentCount}/{classroom.capacity}
            </span>
          </div>
        </div>

        <div className="flex space-x-2">
          <Button
            variant="default"
            size="sm"
            onClick={() => navigate(`/classroom/${classroom.id}`)}
          >
            查看詳情
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(classroom)}
            aria-label="編輯班級"
          >
            <Edit className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onDelete(classroom)}
            disabled={studentCount > 0}
            aria-label="刪除班級"
            title={studentCount > 0 ? '請先移除所有學生' : undefined}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}