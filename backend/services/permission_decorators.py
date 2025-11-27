"""
Permission Decorators

提供基於 Casbin 的權限檢查裝飾器
"""

from functools import wraps
from flask import request, jsonify
from typing import Optional, Callable
from services.casbin_service import get_casbin_service


def require_permission(
    resource: str,
    action: str = "write",
    domain_param: Optional[str] = None,
    use_org_domain: bool = False,
):
    """
    權限檢查裝飾器

    Args:
        resource: 資源名稱（如 'manage_schools', 'manage_teachers'）
        action: 動作（'read' | 'write'，預設 'write'）
        domain_param: 從路徑參數取得 domain 的參數名稱（如 'school_id', 'org_id'）
        use_org_domain: 是否使用機構 domain（如果 True，會從 teacher 的 organization 取得）

    Examples:
        @require_permission('manage_schools', 'write', domain_param='org_id')
        def create_school(org_id):
            # 自動檢查是否有在 org-{org_id} 管理學校的權限
            pass

        @require_permission('manage_teachers', 'write', domain_param='school_id')
        def invite_teacher(school_id):
            # 自動檢查是否有在 school-{school_id} 管理老師的權限
            pass

        @require_permission('view_analytics', 'read', use_org_domain=True)
        def get_org_analytics():
            # 使用當前使用者的機構 domain
            pass
    """

    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 取得當前使用者（從 JWT 或 session）
            teacher_id = getattr(request, "current_teacher_id", None)

            if not teacher_id:
                return (
                    jsonify(
                        {"error": "Unauthorized", "detail": "No teacher_id in request"}
                    ),
                    401,
                )

            # 決定 domain
            domain = _get_domain(teacher_id, domain_param, use_org_domain, kwargs)

            if not domain:
                return (
                    jsonify(
                        {"error": "Bad Request", "detail": "Cannot determine domain"}
                    ),
                    400,
                )

            # 檢查權限
            casbin_service = get_casbin_service()

            if not casbin_service.check_permission(
                teacher_id, domain, resource, action
            ):
                return (
                    jsonify(
                        {
                            "error": "Permission Denied",
                            "detail": f"No permission to {action} {resource} in {domain}",
                        }
                    ),
                    403,
                )

            # 權限檢查通過，執行原函數
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_role(
    *roles: str, domain_param: Optional[str] = None, use_org_domain: bool = False
):
    """
    角色檢查裝飾器（直接檢查角色，不檢查具體權限）

    Args:
        roles: 角色列表（只要有其中一個即可）
        domain_param: 從路徑參數取得 domain 的參數名稱
        use_org_domain: 是否使用機構 domain

    Examples:
        @require_role('org_owner')
        def delete_organization(org_id):
            # 只有 org_owner 可以執行
            pass

        @require_role('org_owner', 'school_admin', domain_param='school_id')
        def update_school(school_id):
            # org_owner 或該校的 school_admin 都可以執行
            pass
    """

    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            teacher_id = getattr(request, "current_teacher_id", None)

            if not teacher_id:
                return jsonify({"error": "Unauthorized"}), 401

            # 決定 domain
            domain = _get_domain(teacher_id, domain_param, use_org_domain, kwargs)

            if not domain:
                return jsonify({"error": "Bad Request"}), 400

            # 檢查是否有任一角色
            casbin_service = get_casbin_service()

            has_role = any(
                casbin_service.has_role(teacher_id, role, domain) for role in roles
            )

            if not has_role:
                return (
                    jsonify(
                        {
                            "error": "Permission Denied",
                            "detail": f"Require one of roles: {roles} in {domain}",
                        }
                    ),
                    403,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_org_owner(domain_param: Optional[str] = None):
    """
    要求 org_owner 角色的裝飾器（簡化版）

    Args:
        domain_param: 從路徑參數取得 org_id 的參數名稱

    Examples:
        @require_org_owner(domain_param='org_id')
        def create_school(org_id):
            pass
    """
    return require_role("org_owner", domain_param=domain_param)


def require_school_admin(domain_param: str):
    """
    要求 school_admin 或 org_owner 角色的裝飾器

    org_owner 可以管理所有學校，所以也通過檢查

    Args:
        domain_param: 從路徑參數取得 school_id 的參數名稱

    Examples:
        @require_school_admin(domain_param='school_id')
        def invite_teacher(school_id):
            pass
    """
    return require_role("org_owner", "school_admin", domain_param=domain_param)


def _get_domain(
    teacher_id: int, domain_param: Optional[str], use_org_domain: bool, kwargs: dict
) -> Optional[str]:
    """
    取得 domain

    Args:
        teacher_id: 老師 ID
        domain_param: domain 參數名稱
        use_org_domain: 是否使用機構 domain
        kwargs: 路徑參數

    Returns:
        domain string 或 None
    """
    # 方案 1: 從路徑參數取得
    if domain_param:
        domain_value = kwargs.get(domain_param)

        if not domain_value:
            print(f"[Permission] Warning: {domain_param} not found in kwargs")
            return None

        # 判斷是 org_id 還是 school_id
        if domain_param == "org_id" or domain_param == "organization_id":
            return f"org-{domain_value}"
        elif domain_param == "school_id":
            return f"school-{domain_value}"
        else:
            # 通用處理：嘗試判斷 domain_value 的格式
            if isinstance(domain_value, str):
                if domain_value.startswith("org-") or domain_value.startswith(
                    "school-"
                ):
                    return domain_value
                else:
                    # 假設是 UUID
                    return f"school-{domain_value}"
            else:
                return f"school-{domain_value}"

    # 方案 2: 使用當前使用者的機構 domain
    if use_org_domain:
        # TODO: Implement after database migrations
        raise NotImplementedError("Org domain lookup pending - requires migrations")

    # 都沒有指定，返回 None
    return None


def get_teacher_permissions(teacher_id: int) -> dict:
    """
    取得老師的所有權限（用於前端顯示）

    Args:
        teacher_id: 老師 ID

    Returns:
        {
            'roles': [
                {'role': 'org_owner', 'domain': 'org-uuid-123'},
                {'role': 'teacher', 'domain': 'school-uuid-456'},
            ],
            'permissions': {
                'org-uuid-123': ['manage_schools', 'manage_teachers', ...],
                'school-uuid-456': ['manage_classrooms', ...]
            }
        }
    """
    casbin_service = get_casbin_service()

    # 取得所有角色
    all_roles = casbin_service.get_all_roles_for_user(teacher_id)

    # 取得每個 domain 的權限
    permissions_by_domain = {}

    for role, domain in all_roles:
        if domain not in permissions_by_domain:
            permissions_by_domain[domain] = set()

        # 根據角色新增權限（簡化版）
        if role == "org_owner":
            permissions_by_domain[domain].update(
                [
                    "manage_organization",
                    "manage_schools",
                    "manage_teachers",
                    "view_analytics",
                    "manage_billing",
                    "manage_classrooms",
                    "view_students",
                ]
            )
        elif role == "school_admin":
            permissions_by_domain[domain].update(
                [
                    "manage_teachers",
                    "view_analytics",
                    "manage_classrooms",
                    "view_students",
                ]
            )
        elif role == "teacher":
            permissions_by_domain[domain].update(
                ["manage_own_classrooms", "view_students", "assign_homework"]
            )

    # 轉換為 list
    permissions_by_domain = {
        domain: list(perms) for domain, perms in permissions_by_domain.items()
    }

    return {
        "roles": [{"role": role, "domain": domain} for role, domain in all_roles],
        "permissions": permissions_by_domain,
    }
