// API configuration
// This value is injected at build time from environment variables
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Helper function for API calls
export const apiCall = async (endpoint: string, options?: RequestInit) => {
  const url = `${API_URL}${endpoint}`
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.status}`)
  }
  
  return response.json()
}