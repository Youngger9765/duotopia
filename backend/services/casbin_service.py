"""
Casbin Permission Service

提供基於 Casbin 的權限管理服務，支援多租戶 RBAC
"""

import casbin
import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

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

    _instance: Optional["CasbinService"] = None
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
        self, teacher_id: int, domain: str, resource: str, action: str
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
        result = self.enforcer.enforce(str(teacher_id), domain, resource, action)

        print(
            f"[Casbin] Check: teacher={teacher_id}, domain={domain}, "
            f"resource={resource}, action={action} => {result}"
        )

        return result

    def has_role(self, teacher_id: int, role: str, domain: str) -> bool:
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
        roles = self.enforcer.get_roles_for_user_in_domain(str(teacher_id), domain)
        return role in roles

    # ============================================
    # 角色管理
    # ============================================

    def add_role_for_user(self, teacher_id: int, role: str, domain: str) -> bool:
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
            str(teacher_id), role, domain
        )

        if success:
            # NOTE: 不儲存到檔案，因為會覆蓋 casbin_policy.csv 中的 p 規則
            # 角色分配（g 規則）應該從資料庫同步，不需要持久化到檔案
            # self.enforcer.save_policy()  # REMOVED: This would overwrite p rules in CSV
            logger.info(
                f"[Casbin] Added role: {role} for teacher={teacher_id} in {domain}"
            )

        return success

    def delete_role_for_user(self, teacher_id: int, role: str, domain: str) -> bool:
        """
        移除使用者的角色

        Args:
            teacher_id: 老師 ID
            role: 角色名稱
            domain: domain ID

        Returns:
            bool: 是否成功
        """
        # Use remove_grouping_policy to delete the g rule: [user, role, domain]
        success = self.enforcer.remove_grouping_policy(str(teacher_id), role, domain)

        if success:
            # NOTE: 不儲存到檔案，因為會覆蓋 casbin_policy.csv 中的 p 規則
            # self.enforcer.save_policy()  # REMOVED: This would overwrite p rules in CSV
            logger.info(
                f"[Casbin] Removed role: {role} for teacher={teacher_id} in {domain}"
            )

        return success

    def delete_all_roles_for_user(
        self, teacher_id: int, domain: Optional[str] = None
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
                # NOTE: 不儲存到檔案，因為會覆蓋 casbin_policy.csv 中的 p 規則
                # self.enforcer.save_policy()  # REMOVED
                logger.info(f"[Casbin] Removed all roles for teacher={teacher_id}")

        return True

    def get_roles_for_user(self, teacher_id: int, domain: str) -> List[str]:
        """
        取得使用者在特定 domain 的所有角色

        Args:
            teacher_id: 老師 ID
            domain: domain ID

        Returns:
            List[str]: 角色列表
        """
        return self.enforcer.get_roles_for_user_in_domain(str(teacher_id), domain)

    def get_all_roles_for_user(self, teacher_id: int) -> List[tuple]:
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

    def sync_from_database(self, db=None):
        """
        從資料庫同步角色到 Casbin (with improved session management)

        Args:
            db: Optional database session (for testing). If None, creates a new session.

        這個方法應該在應用啟動時呼叫，
        將 teacher_organizations 和 teacher_schools 表的資料同步到 Casbin
        """
        from database import get_session_local
        from models.organization import TeacherOrganization, TeacherSchool

        # Use provided session or create a new one
        session_provided = db is not None
        session_to_close = None

        if not session_provided:
            SessionLocal = get_session_local()
            db = SessionLocal()
            session_to_close = db

        try:
            # 1. 只清空角色分配（g rules），保留權限政策（p rules）
            # clear_policy() 會清除所有規則，包括從 CSV 載入的 p 規則
            all_grouping = self.enforcer.get_grouping_policy()
            for g in all_grouping:
                self.enforcer.remove_grouping_policy(*g)
            logger.info(
                f"[Casbin] Cleared {len(all_grouping)} existing role assignments"
            )

            # 2. 同步組織角色
            org_roles = (
                db.query(TeacherOrganization)
                .filter(TeacherOrganization.is_active.is_(True))
                .all()
            )

            for tr in org_roles:
                self.add_role_for_user(
                    tr.teacher_id, tr.role, f"org-{tr.organization_id}"
                )

            logger.info(f"[Casbin] Synced {len(org_roles)} organization roles")

            # 3. 同步學校角色
            school_roles = (
                db.query(TeacherSchool).filter(TeacherSchool.is_active.is_(True)).all()
            )

            for ts in school_roles:
                # TeacherSchool.roles 是列表，需要逐個添加
                if ts.roles:
                    for role in ts.roles:
                        self.add_role_for_user(
                            ts.teacher_id, role, f"school-{ts.school_id}"
                        )

            logger.info(f"[Casbin] Synced {len(school_roles)} school roles")

            # 4. 不需要保存到檔案（會覆蓋 casbin_policy.csv 中的 p 規則）
            # 角色分配只存在記憶體中，每次啟動時從資料庫同步
            # self.enforcer.save_policy()  # REMOVED
            logger.info(
                f"[Casbin] Database sync complete: "
                f"{len(org_roles)} org roles + {len(school_roles)} school roles"
            )

        except Exception as e:
            # Check if error is due to missing tables (e.g., in preview environments)
            error_msg = str(e).lower()
            if (
                "does not exist" in error_msg
                or "no such table" in error_msg
                or "relation" in error_msg
            ):
                logger.warning(
                    f"[Casbin] Organization tables not found in database "
                    f"(expected in preview/staging environments without "
                    f"migrations): {e}"
                )
                logger.info(
                    "[Casbin] Skipping database sync - application will start "
                    "with policy-only permissions"
                )
                # Don't raise - allow application to start without organization roles
            else:
                logger.error(
                    f"[Casbin] Failed to sync from database: {e}", exc_info=True
                )
                raise
        finally:
            if session_to_close is not None:
                try:
                    session_to_close.close()
                except Exception as close_error:
                    logger.error(
                        f"[Casbin] Failed to close database session: {close_error}",
                        exc_info=True,
                    )

    def sync_teacher_roles(self, teacher_id: int, db=None):
        """
        同步特定老師的角色 (with improved session management)

        Args:
            teacher_id: 老師 ID
            db: Optional database session (for testing). If None, creates a new session.
        """
        from database import get_session_local
        from models.organization import TeacherOrganization, TeacherSchool

        # Use provided session or create a new one
        session_provided = db is not None
        session_to_close = None

        if not session_provided:
            SessionLocal = get_session_local()
            db = SessionLocal()
            session_to_close = db

        try:
            # 1. 刪除該教師的所有舊角色
            user = str(teacher_id)

            # Get all grouping policies for this user (format: [user, role, domain])
            all_grouping_policies = self.enforcer.get_grouping_policy()
            removed_count = 0

            for policy in all_grouping_policies:
                if len(policy) >= 3 and policy[0] == user:
                    # policy = [user, role, domain]
                    role = policy[1]
                    domain = policy[2]
                    if self.delete_role_for_user(teacher_id, role, domain):
                        removed_count += 1

            logger.info(
                f"[Casbin] Removed {removed_count} old roles for teacher {teacher_id}"
            )

            # 2. 查詢並添加組織角色
            org_roles = (
                db.query(TeacherOrganization)
                .filter(
                    TeacherOrganization.teacher_id == teacher_id,
                    TeacherOrganization.is_active.is_(True),
                )
                .all()
            )

            for tr in org_roles:
                self.add_role_for_user(teacher_id, tr.role, f"org-{tr.organization_id}")

            logger.info(
                f"[Casbin] Added {len(org_roles)} organization roles for teacher {teacher_id}"
            )

            # 3. 查詢並添加學校角色
            school_roles = (
                db.query(TeacherSchool)
                .filter(
                    TeacherSchool.teacher_id == teacher_id,
                    TeacherSchool.is_active.is_(True),
                )
                .all()
            )

            school_role_count = 0
            for ts in school_roles:
                if ts.roles:
                    for role in ts.roles:
                        self.add_role_for_user(
                            teacher_id, role, f"school-{ts.school_id}"
                        )
                        school_role_count += 1

            logger.info(
                f"[Casbin] Added {school_role_count} school roles for teacher {teacher_id}"
            )
            logger.info(f"[Casbin] Sync complete for teacher {teacher_id}")

        except Exception as e:
            logger.error(
                f"[Casbin] Failed to sync roles for teacher {teacher_id}: {e}",
                exc_info=True,
            )
            raise
        finally:
            if session_to_close is not None:
                try:
                    session_to_close.close()
                except Exception as close_error:
                    logger.error(
                        f"[Casbin] Failed to close database session: {close_error}",
                        exc_info=True,
                    )

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
