export interface User {
  id: number
  email: string
  name?: string
  role?: string
}

export interface Student {
  id?: number
  name: string
  email?: string | null
  birth_date: string
  teacher_id?: number
  class_id?: number
  referrer?: string
  password_status?: 'default' | 'custom'
  created_at?: string
  updated_at?: string
}

export interface Class {
  id: number
  name: string
  grade: string
  capacity: number
  teacher_id: number
  description?: string
  created_at?: string
  updated_at?: string
}

export interface Teacher {
  id: number
  name: string
  email: string
  subject?: string
  created_at?: string
  updated_at?: string
}