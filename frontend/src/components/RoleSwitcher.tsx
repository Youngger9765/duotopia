import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ChevronDown, Building2, User } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { api } from '@/lib/api'

interface RoleInfo {
  primary_role: string
  current_role_context: string
  is_individual_teacher: boolean
  is_institutional_admin: boolean
  has_multiple_roles: boolean
  effective_role: string
}

export function RoleSwitcher() {
  const { toast } = useToast()
  const [roleInfo, setRoleInfo] = useState<RoleInfo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchRoleInfo()
  }, [])

  const fetchRoleInfo = async () => {
    try {
      const response = await api.get('/api/role/current')
      setRoleInfo(response.data)
    } catch (error) {
      console.error('Failed to fetch role info:', error)
    } finally {
      setLoading(false)
    }
  }

  const switchRole = async (context: string) => {
    try {
      const response = await api.post('/api/role/switch', null, {
        params: { context }
      })
      
      // Update token
      localStorage.setItem('token', response.data.access_token)
      
      // Reload the page to update all components
      window.location.reload()
    } catch (error) {
      toast({
        title: "錯誤",
        description: "切換角色失敗",
        variant: "destructive",
      })
    }
  }

  if (loading || !roleInfo || !roleInfo.has_multiple_roles) {
    return null
  }

  const getCurrentRoleDisplay = () => {
    if (roleInfo.current_role_context === 'individual') {
      return {
        label: '個人教師',
        icon: User,
      }
    } else if (roleInfo.current_role_context === 'institutional') {
      return {
        label: '機構管理',
        icon: Building2,
      }
    }
    return {
      label: '預設角色',
      icon: User,
    }
  }

  const currentRole = getCurrentRoleDisplay()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="gap-2">
          <currentRole.icon className="h-4 w-4" />
          {currentRole.label}
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {roleInfo.is_institutional_admin && (
          <DropdownMenuItem 
            onClick={() => switchRole('institutional')}
            className={roleInfo.current_role_context === 'institutional' ? 'bg-accent' : ''}
          >
            <Building2 className="h-4 w-4 mr-2" />
            機構管理
          </DropdownMenuItem>
        )}
        {roleInfo.is_individual_teacher && (
          <DropdownMenuItem 
            onClick={() => switchRole('individual')}
            className={roleInfo.current_role_context === 'individual' ? 'bg-accent' : ''}
          >
            <User className="h-4 w-4 mr-2" />
            個人教師
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}