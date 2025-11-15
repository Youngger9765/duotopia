import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface TeacherUser {
  id: number;
  name: string;
  email: string;
  is_demo?: boolean;
  is_admin?: boolean;
  phone?: string;
}

interface TeacherAuthState {
  token: string | null;
  user: TeacherUser | null;
  isAuthenticated: boolean;
  login: (token: string, user: TeacherUser) => void;
  logout: () => void;
  updateUser: (user: Partial<TeacherUser>) => void;
}

export const useTeacherAuthStore = create<TeacherAuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      login: (token: string, user: TeacherUser) => {
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

      updateUser: (updates: Partial<TeacherUser>) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        }));
      },
    }),
    {
      name: "teacher-auth-storage",
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
