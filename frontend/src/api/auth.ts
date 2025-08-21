import type { User } from '@/types'

export const authApi = {
  login: async (email: string, password: string) => {
    // Mock implementation
    return {
      access_token: 'mock-token',
      user: { id: 1, email } as User,
      roles: ['teacher'],
    }
  },

  validateToken: async (token: string) => {
    // Mock implementation
    return { id: 1, email: 'test@example.com' } as User
  },
}