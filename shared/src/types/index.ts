// User types
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'teacher' | 'student' | 'admin';
  created_at: Date;
  updated_at: Date;
}

// Student types
export interface Student {
  id: string;
  email: string;
  full_name: string;
  birth_date: string;
  parent_email?: string;
  parent_phone?: string;
  created_at: Date;
  updated_at: Date;
}

// Class types
export interface Class {
  id: string;
  name: string;
  grade_level: string;
  difficulty_level: 'preA' | 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';
  teacher_id: string;
  created_at: Date;
  updated_at: Date;
}

// Course types
export interface Course {
  id: string;
  title: string;
  description?: string;
  difficulty_level: 'preA' | 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';
  created_by: string;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}

// Activity types
export type ActivityType = 
  | 'reading_assessment'
  | 'speaking_practice'
  | 'speaking_scenario'
  | 'listening_cloze'
  | 'sentence_making'
  | 'speaking_quiz';

// Lesson types
export interface Lesson {
  id: string;
  course_id: string;
  lesson_number: number;
  title: string;
  activity_type: ActivityType;
  content: any;
  time_limit_minutes: number;
  target_wpm?: number;
  target_accuracy?: number;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}