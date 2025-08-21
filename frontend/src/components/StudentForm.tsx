import React from 'react'
import { useForm } from 'react-hook-form'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/use-toast'

interface Student {
  id?: number
  name: string
  birth_date: string
  email?: string
  referrer?: string
}

interface StudentFormProps {
  isOpen: boolean
  student?: Student
  onSuccess: (student: Student) => void
  onCancel: () => void
}

export const StudentForm: React.FC<StudentFormProps> = ({
  isOpen,
  student,
  onSuccess,
  onCancel,
}) => {
  const { toast } = useToast()
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<Student>({
    defaultValues: student || {},
  })

  const birthDate = watch('birth_date')
  const defaultPassword = birthDate ? birthDate.replace(/-/g, '') : ''

  const onSubmit = (data: Student) => {
    onSuccess(data)
    toast({
      title: student ? '更新成功' : '新增成功',
      description: student
        ? '學生資料已更新'
        : `學生 ${data.name} 已新增，預設密碼：${defaultPassword}`,
    })
  }

  const handleCopyPassword = () => {
    navigator.clipboard.writeText(defaultPassword)
    toast({
      title: '已複製',
      description: '密碼已複製到剪貼簿',
    })
  }

  return (
    <Dialog open={isOpen} onOpenChange={() => onCancel()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{student ? '編輯學生' : '新增學生'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="name">
              姓名 <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              {...register('name', { required: '請輸入學生姓名' })}
            />
            {errors.name && (
              <p className="text-sm text-red-500 mt-1">{errors.name.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="birth_date">
              生日 <span className="text-red-500">*</span>
            </Label>
            <Input
              id="birth_date"
              type="date"
              {...register('birth_date', { required: '請選擇生日' })}
            />
            {errors.birth_date && (
              <p className="text-sm text-red-500 mt-1">
                {errors.birth_date.message}
              </p>
            )}
          </div>

          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              {...register('email', {
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: '請輸入有效的 Email',
                },
              })}
            />
            {errors.email && (
              <p className="text-sm text-red-500 mt-1">{errors.email.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="referrer">推薦人</Label>
            <Input id="referrer" {...register('referrer')} />
          </div>

          {birthDate && !student && (
            <div className="bg-gray-50 p-3 rounded-md flex items-center justify-between">
              <span className="text-sm">預設密碼：{defaultPassword}</span>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleCopyPassword}
                aria-label="複製密碼"
              >
                複製
              </Button>
            </div>
          )}

          <div className="flex justify-end space-x-2">
            <Button type="button" variant="outline" onClick={onCancel}>
              取消
            </Button>
            <Button type="submit">{student ? '更新' : '新增'}</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}