"""
Casbin Permission Service

提供基於 Casbin 的權限管理服務，支援多租戶 RBAC
"""

import os
import casbin
from typing import List, Optional
from pathlib import Path

# 配置檔案路徑（使用绝对路径）
CONFIG_DIR = Path(__file__).parent.parent / "config"
CONFIG_DIR = CONFIG_DIR.resolve()  # 转换为绝对路径
MODEL_PATH = str(CONFIG_DIR / "casbin_model.conf")
POLICY_PATH = str(CONFIG_DIR / "casbin_policy.csv")


class CasbinService:
    """
    Casbin 權限管理服務

    使用 RBAC with Domains 模型支援多租戶權限控制
    """

    _instance: Optional['CasbinService'] = None
    _enforcer: Optional[casbin.Enforcer] = None

    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 Casbin enforcer"""
        if self._enforcer is None:
            self._initialize_enforcer()

    def _initialize_enforcer(self):
        """初始化 enforcer"""
        # 檢查配置檔案是否存在
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Casbin model file not found: {MODEL_PATH}")

        if not os.path.exists(POLICY_PATH):
            raise FileNotFoundError(f"Casbin policy file not found: {POLICY_PATH}")

        # 建立 enforcer（使用記憶體模式）
        self._enforcer = casbin.Enforcer(MODEL_PATH, POLICY_PATH)

        # 載入政策
        self._enforcer.load_policy()

        print(f"[Casbin] Initialized with {self._enforcer.get_policy()} policies")

    @property
    def enforcer(self) -> casbin.Enforcer:
        """取得 enforcer instance"""
        if self._enforcer is None:
            self._initialize_enforcer()
        return self._enforcer

    # ============================================
    # 權限檢查
    # ============================================

    def check_permission(
        self,
        teacher_id: int,
        domain: str,
        resource: str,
        action: str
    ) -> bool:
        """
        檢查權限

        Args:
            teacher_id: 老師 ID
            domain: 'org-{uuid}' 或 'school-{uuid}'
            resource: 資源名稱（如 'manage_schools', 'manage_teachers'）
            action: 動作（'read' | 'write'）

        Returns:
            bool: 是否有權限

        Examples:
            >>> service.check_permission(123, 'org-uuid-abc', 'manage_schools', 'write')
            True
            >>> service.check_permission(123, 'school-uuid-def', 'manage_teachers', 'write')
            False
        """
        result = self.enforcer.enforce(
            str(teacher_id),
            domain,
            resource,
            action
        )

        print(f"[Casbin] Check: teacher={teacher_id}, domain={domain}, "
              f"resource={resource}, action={action} => {result}")

        return result

    def has_role(
        self,
        teacher_id: int,
        role: str,
        domain: str
    ) -> bool:
        """
        檢查使用者在特定 domain 是否有特定角色

        Args:
            teacher_id: 老師 ID
            role: 角色名稱（'org_owner' | 'school_admin' | 'teacher'）
            domain: 'org-{uuid}' 或 'school-{uuid}'

        Returns:
            bool: 是否有該角色

        Examples:
            >>> service.has_role(123, 'org_owner', 'org-uuid-abc')
            True
        """
        # For domain-based RBAC, check if role exists in user's roles for that domain
        roles = self.enforcer.get_roles_for_user_in_domain(
            str(teacher_id),
            domain
        )
        return role in roles

    # ============================================
    # 角色管理
    # ============================================

    def add_role_for_user(
        self,
        teacher_id: int,
        role: str,
        domain: str
    ) -> bool:
        """
        為使用者新增角色

        Args:
            teacher_id: 老師 ID
            role: 角色名稱
            domain: domain ID

        Returns:
            bool: 是否成功
        """
        success = self.enforcer.add_role_for_user_in_domain(
            str(teacher_id),
            role,
            domain
        )

        if success:
            # 儲存變更
            self.enforcer.save_policy()
            print(f"[Casbin] Added role: {role} for teacher={teacher_id} in {domain}")

        return success

    def delete_role_for_user(
        self,
        teacher_id: int,
        role: str,
        domain: str
    ) -> bool:
        """
        移除使用者的角色

        Args:
            teacher_id: 老師 ID
            role: 角色名稱
            domain: domain ID

        Returns:
            bool: 是否成功
        """
        success = self.enforcer.delete_roles_for_user_in_domain(
            str(teacher_id),
            role,
            domain
        )

        if success:
            self.enforcer.save_policy()
            print(f"[Casbin] Removed role: {role} for teacher={teacher_id} in {domain}")

        return success

    def delete_all_roles_for_user(
        self,
        teacher_id: int,
        domain: Optional[str] = None
    ) -> bool:
        """
        移除使用者的所有角色

        Args:
            teacher_id: 老師 ID
            domain: 可選，如果指定只移除該 domain 的角色

        Returns:
            bool: 是否成功
        """
        if domain:
            # 取得使用者在該 domain 的所有角色
            roles = self.get_roles_for_user(teacher_id, domain)
            for role in roles:
                self.delete_role_for_user(teacher_id, role, domain)
        else:
            # 移除所有角色
            success = self.enforcer.delete_roles_for_user(str(teacher_id))
            if success:
                self.enforcer.save_policy()

        return True

    def get_roles_for_user(
        self,
        teacher_id: int,
        domain: str
    ) -> List[str]:
        """
        取得使用者在特定 domain 的所有角色

        Args:
            teacher_id: 老師 ID
            domain: domain ID

        Returns:
            List[str]: 角色列表
        """
        return self.enforcer.get_roles_for_user_in_domain(
            str(teacher_id),
            domain
        )

    def get_all_roles_for_user(
        self,
        teacher_id: int
    ) -> List[tuple]:
        """
        取得使用者在所有 domain 的角色

        Returns:
            List[tuple]: [(role, domain), ...]
        """
        # 取得所有 g 規則
        all_roles = []
        for rule in self.enforcer.get_grouping_policy():
            # rule = [user, role, domain]
            if rule[0] == str(teacher_id):
                all_roles.append((rule[1], rule[2]))

        return all_roles

    # ============================================
    # 資料庫同步
    # ============================================

    def sync_from_database(self):
        """
        從資料庫同步角色到 Casbin

        這個方法應該在應用啟動時呼叫，
        將 teacher_schools 表的資料同步到 Casbin

        TODO: Enable after database migrations are created
        """
        # TODO: Implement after database migrations
        raise NotImplementedError("Database sync pending - requires migrations")

    def sync_teacher_roles(self, teacher_id: int):
        """
        同步特定老師的角色

        Args:
            teacher_id: 老師 ID

        TODO: Enable after database migrations are created
        """
        # TODO: Implement after database migrations
        raise NotImplementedError("Database sync pending - requires migrations")

# ============================================
    # 工具方法
    # ============================================

    def get_all_subjects(self) -> List[str]:
        """取得所有使用者（teacher_id）"""
        subjects = set()
        for rule in self.enforcer.get_grouping_policy():
            subjects.add(rule[0])
        return list(subjects)

    def get_all_domains(self) -> List[str]:
        """取得所有 domains"""
        domains = set()
        for rule in self.enforcer.get_grouping_policy():
            domains.add(rule[2])
        return list(domains)

    def reload_policy(self):
        """重新載入政策檔案"""
        self.enforcer.load_policy()
        print("[Casbin] Policy reloaded")


# ============================================
# 全域 instance
# ============================================

# 建立全域 instance（延遲初始化）
casbin_service: Optional[CasbinService] = None


def get_casbin_service() -> CasbinService:
    """取得 Casbin service instance"""
    global casbin_service
    if casbin_service is None:
        casbin_service = CasbinService()
    return casbin_service


def init_casbin_service():
    """
    初始化 Casbin service

    應該在應用啟動時呼叫
    """
    global casbin_service
    casbin_service = CasbinService()

    # 從資料庫同步角色（如果需要）
    # casbin_service.sync_from_database()

    print("[Casbin] Service initialized")
    return casbin_service
