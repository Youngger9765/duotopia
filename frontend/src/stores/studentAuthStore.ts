import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface StudentUser {
  id: number;
  name: string;
  email: string;
  student_number: string;
  classroom_id: number;
  classroom_name?: string;
  teacher_name?: string;
}

interface StudentAuthState {
  token: string | null;
  user: StudentUser | null;
  isAuthenticated: boolean;
  login: (token: string, user: StudentUser) => void;
  logout: () => void;
  updateUser: (user: Partial<StudentUser>) => void;
}

export const useStudentAuthStore = create<StudentAuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      login: (token: string, user: StudentUser) => {
        set({
          token,
          user,
          isAuthenticated: true,
        });
      },

      logout: () => {
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        });
      },

      updateUser: (updates: Partial<StudentUser>) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        }));
      },
    }),
    {
      name: 'student-auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
