from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_active_user, create_access_token
import models
import schemas
from typing import Optional

router = APIRouter(prefix="/api/role", tags=["role"])

@router.get("/current")
async def get_current_role(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user role context"""
    # Check if it's a dual system user
    if hasattr(current_user, 'is_individual_teacher'):
        return {
            "primary_role": current_user.role.value,
            "current_role_context": current_user.current_role_context,
            "is_individual_teacher": current_user.is_individual_teacher,
            "is_institutional_admin": current_user.is_institutional_admin,
            "has_multiple_roles": current_user.is_individual_teacher and current_user.is_institutional_admin,
            "effective_role": current_user.role.value,
            "full_name": current_user.full_name,
            "email": current_user.email
        }
    else:
        # Regular user
        return {
            "primary_role": current_user.role.value,
            "current_role_context": getattr(current_user, 'current_role_context', 'default'),
            "is_individual_teacher": getattr(current_user, 'is_individual_teacher', False),
            "is_institutional_admin": getattr(current_user, 'is_institutional_admin', False),
            "has_multiple_roles": getattr(current_user, 'has_multiple_roles', False),
            "effective_role": current_user.role.value,
            "full_name": current_user.full_name,
            "email": current_user.email
        }

@router.post("/switch")
async def switch_role_context(
    context: str,  # "individual" or "institutional" or "default"
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Switch user role context"""
    # Validate context
    if context not in ["individual", "institutional", "default"]:
        raise HTTPException(status_code=400, detail="Invalid role context")
    
    # Check if it's a dual system user
    if hasattr(current_user, 'is_individual_teacher'):
        # Check if user has permission for the requested context
        if context == "individual" and not current_user.is_individual_teacher:
            raise HTTPException(status_code=403, detail="User doesn't have individual teacher role")
        
        if context == "institutional" and not current_user.is_institutional_admin:
            raise HTTPException(status_code=403, detail="User doesn't have institutional admin role")
        
        # Update user's current role context
        current_user.current_role_context = context
        db.commit()
        db.refresh(current_user)
    else:
        # Regular user - can't switch contexts
        if context != "default":
            raise HTTPException(status_code=403, detail="Regular users cannot switch role contexts")
    
    # Create new token with updated context
    access_token = create_access_token(
        data={
            "sub": current_user.email,
            "role_context": context
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role_context": context,
        "effective_role": current_user.role.value
    }

@router.post("/update-capabilities")
async def update_user_capabilities(
    user_id: str,
    is_individual_teacher: Optional[bool] = None,
    is_institutional_admin: Optional[bool] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user role capabilities (admin only)"""
    # Only system admins can update role capabilities
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update role capabilities")
    
    # Find the user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update capabilities
    if is_individual_teacher is not None:
        user.is_individual_teacher = is_individual_teacher
    
    if is_institutional_admin is not None:
        user.is_institutional_admin = is_institutional_admin
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "is_individual_teacher": user.is_individual_teacher,
        "is_institutional_admin": user.is_institutional_admin,
        "has_multiple_roles": user.has_multiple_roles
    }