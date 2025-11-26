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
        # 清空政策
        self.casbin.enforcer.clear_policy()
        yield
        # 清理
        self.casbin.enforcer.clear_policy()

    def test_add_and_check_role(self):
        """測試新增角色並檢查"""
        # 新增機構層級角色
        success = self.casbin.add_role_for_user(
            teacher_id=123,
            role='org_owner',
            domain='org-test-uuid'
        )

        assert success == True

        # 檢查角色（使用 has_role 方法）
        has_role = self.casbin.has_role(
            teacher_id=123,
            role='org_owner',
            domain='org-test-uuid'
        )

        assert has_role == True

    def test_check_permission_org_owner(self):
        """測試 org_owner 權限"""
        # 新增角色
        self.casbin.add_role_for_user(123, 'org_owner', 'org-test')

        # 檢查權限（org_owner 可以管理學校）
        can_manage_schools = self.casbin.check_permission(
            teacher_id=123,
            domain='org-test',
            resource='manage_schools',
            action='write'
        )

        assert can_manage_schools == True

        # org_owner 也可以管理老師
        can_manage_teachers = self.casbin.check_permission(
            teacher_id=123,
            domain='org-test',
            resource='manage_teachers',
            action='write'
        )

        assert can_manage_teachers == True

    def test_check_permission_school_admin(self):
        """測試 school_admin 權限"""
        # 新增角色
        self.casbin.add_role_for_user(456, 'school_admin', 'school-test')

        # school_admin 可以管理老師
        can_manage_teachers = self.casbin.check_permission(
            teacher_id=456,
            domain='school-test',
            resource='manage_teachers',
            action='write'
        )

        assert can_manage_teachers == True

        # school_admin 不能管理學校（只有 org_owner 可以）
        can_manage_schools = self.casbin.check_permission(
            teacher_id=456,
            domain='school-test',
            resource='manage_schools',
            action='write'
        )

        assert can_manage_schools == False

    def test_check_permission_teacher(self):
        """測試 teacher 權限"""
        # 新增角色
        self.casbin.add_role_for_user(789, 'teacher', 'school-test')

        # teacher 可以管理自己的班級
        can_manage_classrooms = self.casbin.check_permission(
            teacher_id=789,
            domain='school-test',
            resource='manage_own_classrooms',
            action='write'
        )

        assert can_manage_classrooms == True

        # teacher 不能管理老師
        can_manage_teachers = self.casbin.check_permission(
            teacher_id=789,
            domain='school-test',
            resource='manage_teachers',
            action='write'
        )

        assert can_manage_teachers == False

    def test_wildcard_domain(self):
        """測試 wildcard domain (org_owner 可以管理所有學校)"""
        # 新增機構層級角色
        self.casbin.add_role_for_user(123, 'org_owner', 'org-test')

        # org_owner 在機構 domain 可以管理學校
        can_manage = self.casbin.check_permission(
            teacher_id=123,
            domain='org-test',
            resource='manage_schools',
            action='write'
        )

        assert can_manage == True

    def test_delete_role(self):
        """測試刪除角色"""
        # 新增角色
        self.casbin.add_role_for_user(123, 'teacher', 'school-test')

        # 確認有角色
        assert self.casbin.has_role(123, 'teacher', 'school-test') == True

        # 刪除角色
        success = self.casbin.delete_role_for_user(123, 'teacher', 'school-test')

        assert success == True

        # 確認已刪除
        assert self.casbin.has_role(123, 'teacher', 'school-test') == False

    def test_get_roles_for_user(self):
        """測試取得使用者角色"""
        # 新增多個角色
        self.casbin.add_role_for_user(123, 'org_owner', 'org-test')
        self.casbin.add_role_for_user(123, 'school_admin', 'school-test1')
        self.casbin.add_role_for_user(123, 'teacher', 'school-test2')

        # 取得機構層級角色
        org_roles = self.casbin.get_roles_for_user(123, 'org-test')
        assert 'org_owner' in org_roles

        # 取得學校層級角色
        school_roles = self.casbin.get_roles_for_user(123, 'school-test1')
        assert 'school_admin' in school_roles

        # 取得所有角色
        all_roles = self.casbin.get_all_roles_for_user(123)
        assert len(all_roles) == 3
        assert ('org_owner', 'org-test') in all_roles
        assert ('school_admin', 'school-test1') in all_roles
        assert ('teacher', 'school-test2') in all_roles

    def test_delete_all_roles(self):
        """測試刪除所有角色"""
        # 新增多個角色
        self.casbin.add_role_for_user(123, 'org_owner', 'org-test')
        self.casbin.add_role_for_user(123, 'teacher', 'school-test')

        # 刪除所有角色
        self.casbin.delete_all_roles_for_user(123)

        # 確認都已刪除
        all_roles = self.casbin.get_all_roles_for_user(123)
        assert len(all_roles) == 0

    def test_multiple_users_same_domain(self):
        """測試多個使用者在同一 domain"""
        # User 1: org_owner
        self.casbin.add_role_for_user(123, 'org_owner', 'org-test')

        # User 2: school_admin
        self.casbin.add_role_for_user(456, 'school_admin', 'org-test')

        # User 3: teacher
        self.casbin.add_role_for_user(789, 'teacher', 'org-test')

        # 驗證各自的權限
        assert self.casbin.check_permission(123, 'org-test', 'manage_schools', 'write') == True
        assert self.casbin.check_permission(456, 'org-test', 'manage_schools', 'write') == False
        assert self.casbin.check_permission(789, 'org-test', 'manage_schools', 'write') == False

        assert self.casbin.check_permission(123, 'org-test', 'manage_teachers', 'write') == True
        assert self.casbin.check_permission(456, 'org-test', 'manage_teachers', 'write') == True
        assert self.casbin.check_permission(789, 'org-test', 'manage_teachers', 'write') == False

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


# 如果要測試資料庫同步，需要 mock database
@pytest.mark.skip(reason="需要資料庫連線")
class TestDatabaseSync:
    """測試資料庫同步（需要資料庫）"""

    def test_sync_from_database(self):
        """測試從資料庫同步"""
        # TODO: 實作資料庫 mock
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
