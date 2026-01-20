"""
Casbin Integration Tests

測試 Casbin 權限系統的整合
"""

import pytest
from services.casbin_service import CasbinService, get_casbin_service


class TestCasbinService:
    """測試 CasbinService"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每個測試前初始化"""
        self.casbin = CasbinService()
        # 只清空角色分配（g rules），保留權限政策（p rules）
        # clear_policy() 會清除所有規則，包括從 CSV 載入的 p 規則
        # 我們只想清除測試中動態添加的角色分配
        all_grouping = self.casbin.enforcer.get_grouping_policy()
        for g in all_grouping:
            self.casbin.enforcer.remove_grouping_policy(*g)
        yield
        # 清理：只清除角色分配
        all_grouping = self.casbin.enforcer.get_grouping_policy()
        for g in all_grouping:
            self.casbin.enforcer.remove_grouping_policy(*g)

    def test_add_and_check_role(self):
        """測試新增角色並檢查"""
        # 新增機構層級角色
        success = self.casbin.add_role_for_user(
            teacher_id=123, role="org_owner", domain="org-test-uuid"
        )

        assert success is True

        # 檢查角色（使用 has_role 方法）
        has_role = self.casbin.has_role(
            teacher_id=123, role="org_owner", domain="org-test-uuid"
        )

        assert has_role is True

    def test_check_permission_org_owner(self):
        """測試 org_owner 權限"""
        # 新增角色
        self.casbin.add_role_for_user(123, "org_owner", "org-test")

        # 檢查權限（org_owner 可以管理學校）
        can_manage_schools = self.casbin.check_permission(
            teacher_id=123, domain="org-test", resource="manage_schools", action="write"
        )

        assert can_manage_schools is True

        # org_owner 也可以管理老師
        can_manage_teachers = self.casbin.check_permission(
            teacher_id=123,
            domain="org-test",
            resource="manage_teachers",
            action="write",
        )

        assert can_manage_teachers is True

    def test_check_permission_school_admin(self):
        """測試 school_admin 權限"""
        # 新增角色
        self.casbin.add_role_for_user(456, "school_admin", "school-test")

        # school_admin 可以管理老師
        can_manage_teachers = self.casbin.check_permission(
            teacher_id=456,
            domain="school-test",
            resource="manage_teachers",
            action="write",
        )

        assert can_manage_teachers is True

        # school_admin 不能管理學校（只有 org_owner 可以）
        can_manage_schools = self.casbin.check_permission(
            teacher_id=456,
            domain="school-test",
            resource="manage_schools",
            action="write",
        )

        assert can_manage_schools is False

    def test_check_permission_teacher(self):
        """測試 teacher 權限"""
        # 新增角色
        self.casbin.add_role_for_user(789, "teacher", "school-test")

        # teacher 可以管理自己的班級
        can_manage_classrooms = self.casbin.check_permission(
            teacher_id=789,
            domain="school-test",
            resource="manage_own_classrooms",
            action="write",
        )

        assert can_manage_classrooms is True

        # teacher 不能管理老師
        can_manage_teachers = self.casbin.check_permission(
            teacher_id=789,
            domain="school-test",
            resource="manage_teachers",
            action="write",
        )

        assert can_manage_teachers is False

    def test_wildcard_domain(self):
        """測試 wildcard domain (org_owner 可以管理所有學校)"""
        # 新增機構層級角色
        self.casbin.add_role_for_user(123, "org_owner", "org-test")

        # org_owner 在機構 domain 可以管理學校
        can_manage = self.casbin.check_permission(
            teacher_id=123, domain="org-test", resource="manage_schools", action="write"
        )

        assert can_manage is True

    def test_delete_role(self):
        """測試刪除角色"""
        # 新增角色
        self.casbin.add_role_for_user(123, "teacher", "school-test")

        # 確認有角色
        assert self.casbin.has_role(123, "teacher", "school-test") is True

        # 刪除角色
        success = self.casbin.delete_role_for_user(123, "teacher", "school-test")

        assert success is True

        # 確認已刪除
        assert self.casbin.has_role(123, "teacher", "school-test") is False

    def test_get_roles_for_user(self):
        """測試取得使用者角色"""
        # 新增多個角色
        self.casbin.add_role_for_user(123, "org_owner", "org-test")
        self.casbin.add_role_for_user(123, "school_admin", "school-test1")
        self.casbin.add_role_for_user(123, "teacher", "school-test2")

        # 取得機構層級角色
        org_roles = self.casbin.get_roles_for_user(123, "org-test")
        assert "org_owner" in org_roles

        # 取得學校層級角色
        school_roles = self.casbin.get_roles_for_user(123, "school-test1")
        assert "school_admin" in school_roles

        # 取得所有角色
        all_roles = self.casbin.get_all_roles_for_user(123)
        assert len(all_roles) == 3
        assert ("org_owner", "org-test") in all_roles
        assert ("school_admin", "school-test1") in all_roles
        assert ("teacher", "school-test2") in all_roles

    def test_delete_all_roles(self):
        """測試刪除所有角色"""
        # 新增多個角色
        self.casbin.add_role_for_user(123, "org_owner", "org-test")
        self.casbin.add_role_for_user(123, "teacher", "school-test")

        # 刪除所有角色
        self.casbin.delete_all_roles_for_user(123)

        # 確認都已刪除
        all_roles = self.casbin.get_all_roles_for_user(123)
        assert len(all_roles) == 0

    def test_multiple_users_same_domain(self):
        """測試多個使用者在同一 domain"""
        # User 1: org_owner
        self.casbin.add_role_for_user(123, "org_owner", "org-test")

        # User 2: school_admin
        self.casbin.add_role_for_user(456, "school_admin", "org-test")

        # User 3: teacher
        self.casbin.add_role_for_user(789, "teacher", "org-test")

        # 驗證各自的權限
        assert (
            self.casbin.check_permission(123, "org-test", "manage_schools", "write")
            is True
        )
        assert (
            self.casbin.check_permission(456, "org-test", "manage_schools", "write")
            is False
        )
        assert (
            self.casbin.check_permission(789, "org-test", "manage_schools", "write")
            is False
        )

        assert (
            self.casbin.check_permission(123, "org-test", "manage_teachers", "write")
            is True
        )
        assert (
            self.casbin.check_permission(456, "org-test", "manage_teachers", "write")
            is True
        )
        assert (
            self.casbin.check_permission(789, "org-test", "manage_teachers", "write")
            is False
        )

    def test_singleton_pattern(self):
        """測試單例模式"""
        service1 = CasbinService()
        service2 = CasbinService()
        service3 = get_casbin_service()

        # 應該是同一個 instance
        assert service1 is service2
        assert service2 is service3


class TestCasbinHelpers:
    """測試輔助函數"""

    def test_get_casbin_service(self):
        """測試取得 service"""
        service = get_casbin_service()

        assert service is not None
        assert isinstance(service, CasbinService)
        assert service.enforcer is not None


class TestDatabaseSync:
    """測試資料庫同步功能"""

    @pytest.fixture(autouse=True)
    def setup(self, shared_test_session):
        """每個測試前初始化"""
        self.db = shared_test_session
        self.casbin = CasbinService()
        # 清空 Casbin 政策
        self.casbin.enforcer.clear_policy()
        yield
        # 清理
        self.casbin.enforcer.clear_policy()

    def test_sync_from_database_empty(self):
        """測試從空資料庫同步"""
        # 確保資料庫為空
        from models.organization import TeacherOrganization, TeacherSchool

        assert self.db.query(TeacherOrganization).count() == 0
        assert self.db.query(TeacherSchool).count() == 0

        # 同步應該成功且無錯誤
        self.casbin.sync_from_database(db=self.db)

        # 驗證沒有角色
        all_policies = self.casbin.enforcer.get_grouping_policy()
        assert len(all_policies) == 0

    def test_sync_from_database_with_org_roles(self):
        """測試同步組織角色"""
        from models.organization import Organization, TeacherOrganization
        from tests.factories import TestDataFactory
        import uuid

        # 創建測試資料
        teacher = TestDataFactory.create_teacher(self.db)
        self.db.flush()

        org = Organization(
            id=uuid.uuid4(), name="Test Org", display_name="Test Organization"
        )
        self.db.add(org)
        self.db.flush()

        teacher_org = TeacherOrganization(
            teacher_id=teacher.id,
            organization_id=org.id,
            role="org_owner",
            is_active=True,
        )
        self.db.add(teacher_org)
        self.db.commit()

        # 執行同步
        self.casbin.sync_from_database(db=self.db)

        # 驗證角色已同步
        has_role = self.casbin.has_role(teacher.id, "org_owner", f"org-{org.id}")
        assert has_role is True

        # 驗證權限
        can_manage_schools = self.casbin.check_permission(
            teacher.id, f"org-{org.id}", "manage_schools", "write"
        )
        assert can_manage_schools is True

    def test_sync_from_database_with_school_roles(self):
        """測試同步學校角色"""
        from models.organization import Organization, School, TeacherSchool
        from tests.factories import TeacherFactory
        import uuid

        # 創建測試資料
        teacher = TeacherFactory.create()
        self.db.add(teacher)

        org = Organization(id=uuid.uuid4(), name="Test Org")
        self.db.add(org)
        self.db.flush()

        school = School(id=uuid.uuid4(), organization_id=org.id, name="Test School")
        self.db.add(school)
        self.db.flush()

        teacher_school = TeacherSchool(
            teacher_id=teacher.id,
            school_id=school.id,
            roles=["school_admin", "teacher"],
            is_active=True,
        )
        self.db.add(teacher_school)
        self.db.commit()

        # 執行同步
        self.casbin.sync_from_database(db=self.db)

        # 驗證兩個角色都已同步
        has_admin_role = self.casbin.has_role(
            teacher.id, "school_admin", f"school-{school.id}"
        )
        has_teacher_role = self.casbin.has_role(
            teacher.id, "teacher", f"school-{school.id}"
        )
        assert has_admin_role is True
        assert has_teacher_role is True

    def test_sync_from_database_ignores_inactive(self):
        """測試同步時忽略 is_active=False 的記錄"""
        from models.organization import Organization, TeacherOrganization
        from tests.factories import TeacherFactory
        import uuid

        # 創建測試資料
        teacher = TeacherFactory.create()
        self.db.add(teacher)

        org = Organization(id=uuid.uuid4(), name="Test Org")
        self.db.add(org)
        self.db.flush()

        # 創建 inactive 的角色
        teacher_org = TeacherOrganization(
            teacher_id=teacher.id,
            organization_id=org.id,
            role="org_owner",
            is_active=False,  # Inactive!
        )
        self.db.add(teacher_org)
        self.db.commit()

        # 執行同步
        self.casbin.sync_from_database(db=self.db)

        # 驗證 inactive 角色未被同步
        has_role = self.casbin.has_role(teacher.id, "org_owner", f"org-{org.id}")
        assert has_role is False

    def test_sync_teacher_roles(self):
        """測試同步特定教師的角色"""
        from models.organization import (
            Organization,
            School,
            TeacherOrganization,
            TeacherSchool,
        )
        from tests.factories import TeacherFactory
        import uuid

        # 創建測試資料
        teacher = TeacherFactory.create()
        self.db.add(teacher)

        org = Organization(id=uuid.uuid4(), name="Test Org")
        self.db.add(org)
        self.db.flush()

        school = School(id=uuid.uuid4(), organization_id=org.id, name="Test School")
        self.db.add(school)
        self.db.flush()

        # 添加組織角色
        teacher_org = TeacherOrganization(
            teacher_id=teacher.id,
            organization_id=org.id,
            role="org_owner",
            is_active=True,
        )
        self.db.add(teacher_org)

        # 添加學校角色
        teacher_school = TeacherSchool(
            teacher_id=teacher.id,
            school_id=school.id,
            roles=["teacher"],
            is_active=True,
        )
        self.db.add(teacher_school)
        self.db.commit()

        # 執行同步（針對特定教師）
        self.casbin.sync_teacher_roles(teacher.id, db=self.db)

        # 驗證角色已同步
        has_org_role = self.casbin.has_role(teacher.id, "org_owner", f"org-{org.id}")
        has_school_role = self.casbin.has_role(
            teacher.id, "teacher", f"school-{school.id}"
        )
        assert has_org_role is True
        assert has_school_role is True

    def test_sync_teacher_roles_removes_old_roles(self):
        """測試 sync_teacher_roles 會移除舊角色"""
        from models.organization import Organization, TeacherOrganization
        from tests.factories import TeacherFactory
        import uuid

        # 創建測試資料
        teacher = TeacherFactory.create()
        self.db.add(teacher)

        org = Organization(id=uuid.uuid4(), name="Test Org")
        self.db.add(org)
        self.db.flush()

        # 先手動添加一個 Casbin 角色
        self.casbin.add_role_for_user(teacher.id, "old_role", f"org-{org.id}")
        assert self.casbin.has_role(teacher.id, "old_role", f"org-{org.id}") is True

        # 在資料庫中創建新角色（不包含 old_role）
        teacher_org = TeacherOrganization(
            teacher_id=teacher.id,
            organization_id=org.id,
            role="org_owner",
            is_active=True,
        )
        self.db.add(teacher_org)
        self.db.commit()

        # 執行同步
        self.casbin.sync_teacher_roles(teacher.id, db=self.db)

        # 驗證舊角色已移除
        has_old_role = self.casbin.has_role(teacher.id, "old_role", f"org-{org.id}")
        assert has_old_role is False

        # 驗證新角色已添加
        has_new_role = self.casbin.has_role(teacher.id, "org_owner", f"org-{org.id}")
        assert has_new_role is True

    def test_sync_teacher_roles_handles_role_changes(self):
        """測試 sync_teacher_roles 處理角色變更"""
        from models.organization import School, TeacherSchool, Organization
        from tests.factories import TeacherFactory
        import uuid

        # 創建測試資料
        teacher = TeacherFactory.create()
        self.db.add(teacher)

        org = Organization(id=uuid.uuid4(), name="Test Org")
        self.db.add(org)
        self.db.flush()

        school = School(id=uuid.uuid4(), organization_id=org.id, name="Test School")
        self.db.add(school)
        self.db.flush()

        # 初始角色: teacher
        teacher_school = TeacherSchool(
            teacher_id=teacher.id,
            school_id=school.id,
            roles=["teacher"],
            is_active=True,
        )
        self.db.add(teacher_school)
        self.db.commit()

        # 第一次同步
        self.casbin.sync_teacher_roles(teacher.id, db=self.db)
        assert (
            self.casbin.has_role(teacher.id, "teacher", f"school-{school.id}") is True
        )
        assert (
            self.casbin.has_role(teacher.id, "school_admin", f"school-{school.id}")
            is False
        )

        # 升級為 school_admin
        teacher_school.roles = ["school_admin", "teacher"]
        self.db.commit()

        # 第二次同步
        self.casbin.sync_teacher_roles(teacher.id, db=self.db)
        assert (
            self.casbin.has_role(teacher.id, "teacher", f"school-{school.id}") is True
        )
        assert (
            self.casbin.has_role(teacher.id, "school_admin", f"school-{school.id}")
            is True
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
