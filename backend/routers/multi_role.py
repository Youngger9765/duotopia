"""
多重角色管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel

from database import get_db
from models_multi_role import User, UserInstitutionRole, School, InstitutionRole, RoleChecker
from auth import get_current_user
import json

router = APIRouter(
    prefix="/api/roles",
    tags=["multi-role-management"]
)

# Pydantic 模型
class RoleAssignmentRequest(BaseModel):
    roles: List[str]
    permissions: Optional[Dict[str, Any]] = {}
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class RoleAssignmentResponse(BaseModel):
    id: str
    user_id: str
    institution_id: str
    institution_name: str
    roles: List[str]
    permissions: Dict[str, Any]
    is_active: bool
    start_date: date
    end_date: Optional[date]
    created_at: datetime

class UserRolesSummary(BaseModel):
    user_id: str
    email: str
    full_name: str
    platform_role: str
    institution_roles: List[RoleAssignmentResponse]

# 角色管理 API 端點

@router.get("/users/{user_id}", response_model=UserRolesSummary)
async def get_user_all_roles(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取用戶所有角色（平台 + 所有機構）"""
    
    # 權限檢查：只有平台管理員或本人可以查看
    if not RoleChecker.has_platform_admin(current_user) and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="無權限查看此用戶的角色信息")
    
    # 獲取用戶基本信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    # 獲取用戶所有機構角色
    institution_roles = db.query(UserInstitutionRole).join(School).filter(
        UserInstitutionRole.user_id == user_id
    ).all()
    
    role_responses = []
    for role in institution_roles:
        role_responses.append(RoleAssignmentResponse(
            id=role.id,
            user_id=role.user_id,
            institution_id=role.institution_id,
            institution_name=role.institution.name,
            roles=role.roles,
            permissions=role.permissions or {},
            is_active=role.is_active,
            start_date=role.start_date,
            end_date=role.end_date,
            created_at=role.created_at
        ))
    
    return UserRolesSummary(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        platform_role=user.platform_role,
        institution_roles=role_responses
    )

@router.get("/users/{user_id}/institutions/{institution_id}", response_model=RoleAssignmentResponse)
async def get_user_institution_roles(
    user_id: str,
    institution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取用戶在特定機構的角色"""
    
    # 權限檢查
    if not (RoleChecker.has_platform_admin(current_user) or 
            current_user.id == user_id or
            RoleChecker.has_institution_role(current_user.id, institution_id, "admin")):
        raise HTTPException(status_code=403, detail="無權限查看此角色信息")
    
    role = db.query(UserInstitutionRole).join(School).filter(
        UserInstitutionRole.user_id == user_id,
        UserInstitutionRole.institution_id == institution_id
    ).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="未找到角色記錄")
    
    return RoleAssignmentResponse(
        id=role.id,
        user_id=role.user_id,
        institution_id=role.institution_id,
        institution_name=role.institution.name,
        roles=role.roles,
        permissions=role.permissions or {},
        is_active=role.is_active,
        start_date=role.start_date,
        end_date=role.end_date,
        created_at=role.created_at
    )

@router.post("/users/{user_id}/institutions/{institution_id}", response_model=RoleAssignmentResponse)
async def assign_user_roles(
    user_id: str,
    institution_id: str,
    role_request: RoleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """為用戶在特定機構分配角色"""
    
    # 權限檢查：只有平台管理員或機構管理員可以分配角色
    if not (RoleChecker.has_platform_admin(current_user) or 
            RoleChecker.has_institution_role(current_user.id, institution_id, "admin")):
        raise HTTPException(status_code=403, detail="無權限分配角色")
    
    # 驗證用戶和機構存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    institution = db.query(School).filter(School.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="機構不存在")
    
    # 驗證角色有效性
    valid_roles = [role.value for role in InstitutionRole]
    invalid_roles = [role for role in role_request.roles if role not in valid_roles]
    if invalid_roles:
        raise HTTPException(status_code=400, detail=f"無效的角色: {invalid_roles}")
    
    # 檢查是否已有角色記錄
    existing_role = db.query(UserInstitutionRole).filter(
        UserInstitutionRole.user_id == user_id,
        UserInstitutionRole.institution_id == institution_id
    ).first()
    
    if existing_role:
        raise HTTPException(status_code=400, detail="用戶在此機構已有角色，請使用更新接口")
    
    # 創建新的角色記錄
    new_role = UserInstitutionRole(
        user_id=user_id,
        institution_id=institution_id,
        roles=role_request.roles,
        permissions=role_request.permissions,
        start_date=role_request.start_date or date.today(),
        end_date=role_request.end_date,
        created_by=current_user.id
    )
    
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    return RoleAssignmentResponse(
        id=new_role.id,
        user_id=new_role.user_id,
        institution_id=new_role.institution_id,
        institution_name=institution.name,
        roles=new_role.roles,
        permissions=new_role.permissions or {},
        is_active=new_role.is_active,
        start_date=new_role.start_date,
        end_date=new_role.end_date,
        created_at=new_role.created_at
    )

@router.put("/users/{user_id}/institutions/{institution_id}", response_model=RoleAssignmentResponse)
async def update_user_roles(
    user_id: str,
    institution_id: str,
    role_request: RoleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用戶在特定機構的角色"""
    
    # 權限檢查
    if not (RoleChecker.has_platform_admin(current_user) or 
            RoleChecker.has_institution_role(current_user.id, institution_id, "admin")):
        raise HTTPException(status_code=403, detail="無權限更新角色")
    
    # 查找現有角色記錄
    role_record = db.query(UserInstitutionRole).join(School).filter(
        UserInstitutionRole.user_id == user_id,
        UserInstitutionRole.institution_id == institution_id
    ).first()
    
    if not role_record:
        raise HTTPException(status_code=404, detail="未找到角色記錄")
    
    # 驗證角色有效性
    valid_roles = [role.value for role in InstitutionRole]
    invalid_roles = [role for role in role_request.roles if role not in valid_roles]
    if invalid_roles:
        raise HTTPException(status_code=400, detail=f"無效的角色: {invalid_roles}")
    
    # 更新角色信息
    role_record.roles = role_request.roles
    if role_request.permissions is not None:
        role_record.permissions = role_request.permissions
    if role_request.start_date is not None:
        role_record.start_date = role_request.start_date
    if role_request.end_date is not None:
        role_record.end_date = role_request.end_date
    
    role_record.updated_at = datetime.now()
    
    db.commit()
    db.refresh(role_record)
    
    return RoleAssignmentResponse(
        id=role_record.id,
        user_id=role_record.user_id,
        institution_id=role_record.institution_id,
        institution_name=role_record.institution.name,
        roles=role_record.roles,
        permissions=role_record.permissions or {},
        is_active=role_record.is_active,
        start_date=role_record.start_date,
        end_date=role_record.end_date,
        created_at=role_record.created_at
    )

@router.patch("/users/{user_id}/institutions/{institution_id}/status")
async def toggle_role_status(
    user_id: str,
    institution_id: str,
    active: bool = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """啟用/停用用戶角色"""
    
    # 權限檢查
    if not (RoleChecker.has_platform_admin(current_user) or 
            RoleChecker.has_institution_role(current_user.id, institution_id, "admin")):
        raise HTTPException(status_code=403, detail="無權限修改角色狀態")
    
    role_record = db.query(UserInstitutionRole).filter(
        UserInstitutionRole.user_id == user_id,
        UserInstitutionRole.institution_id == institution_id
    ).first()
    
    if not role_record:
        raise HTTPException(status_code=404, detail="未找到角色記錄")
    
    role_record.is_active = active
    role_record.updated_at = datetime.now()
    
    db.commit()
    
    return {"message": f"角色已{'啟用' if active else '停用'}"}

@router.delete("/users/{user_id}/institutions/{institution_id}")
async def revoke_user_roles(
    user_id: str,
    institution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """撤銷用戶在特定機構的所有角色"""
    
    # 權限檢查
    if not (RoleChecker.has_platform_admin(current_user) or 
            RoleChecker.has_institution_role(current_user.id, institution_id, "admin")):
        raise HTTPException(status_code=403, detail="無權限撤銷角色")
    
    role_record = db.query(UserInstitutionRole).filter(
        UserInstitutionRole.user_id == user_id,
        UserInstitutionRole.institution_id == institution_id
    ).first()
    
    if not role_record:
        raise HTTPException(status_code=404, detail="未找到角色記錄")
    
    db.delete(role_record)
    db.commit()
    
    return {"message": "角色已撤銷"}

@router.get("/institutions/{institution_id}/users")
async def get_institution_users(
    institution_id: str,
    role_filter: Optional[str] = Query(None, description="過濾特定角色的用戶"),
    active_only: bool = Query(True, description="只返回啟用的角色"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取機構內所有用戶及其角色"""
    
    # 權限檢查
    if not (RoleChecker.has_platform_admin(current_user) or 
            RoleChecker.has_institution_role(current_user.id, institution_id, "admin")):
        raise HTTPException(status_code=403, detail="無權限查看機構用戶")
    
    query = db.query(UserInstitutionRole).join(User).filter(
        UserInstitutionRole.institution_id == institution_id
    )
    
    if active_only:
        query = query.filter(UserInstitutionRole.is_active == True)
    
    role_records = query.all()
    
    result = []
    for role in role_records:
        # 如果指定了角色過濾，檢查是否匹配
        if role_filter and role_filter not in role.roles:
            continue
            
        result.append({
            "user_id": role.user.id,
            "email": role.user.email,
            "full_name": role.user.full_name,
            "roles": role.roles,
            "permissions": role.permissions or {},
            "is_active": role.is_active,
            "start_date": role.start_date,
            "end_date": role.end_date
        })
    
    return {"institution_id": institution_id, "users": result}

@router.get("/check-permission/{user_id}")
async def check_user_permission(
    user_id: str,
    institution_id: str = Query(...),
    action: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """檢查用戶權限"""
    
    # 權限檢查：只有平台管理員、機構管理員或本人可以查看
    if not (RoleChecker.has_platform_admin(current_user) or 
            current_user.id == user_id or
            RoleChecker.has_institution_role(current_user.id, institution_id, "admin")):
        raise HTTPException(status_code=403, detail="無權限檢查此權限")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    has_permission = RoleChecker.can_access_resource(user, institution_id, action)
    
    return {
        "user_id": user_id,
        "institution_id": institution_id, 
        "action": action,
        "has_permission": has_permission
    }