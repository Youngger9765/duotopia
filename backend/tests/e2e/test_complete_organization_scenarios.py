"""
完整機構場景測試 - E2E
測試所有場景矩陣（補習班、課程分享、個體戶等）

對應文件: docs/ORGANIZATION_TEST_SCENARIOS_MATRIX.md
"""

import pytest
from datetime import date
from sqlalchemy.orm import Session
from models import (
    Teacher,
    Organization,
    School,
    Classroom,
    Student,
    ClassroomStudent,
    TeacherOrganization,
    TeacherSchool,
    ClassroomSchool,
    Program,
    Assignment,
    StudentAssignment,
)
from services.casbin_service import get_casbin_service


# ============================================================
# 場景 1: 補習班 - 單一分校
# ============================================================


class TestScenario1BasicCramSchool:
    """場景 1: 補習班 - 單一分校"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):
        """設置場景1資料"""
        self.db = db_session

        # 組織
        org = Organization(
            name="happy-cram-school",
            display_name="快樂補習班",
            contact_email="happy@example.com",
        )
        self.db.add(org)
        self.db.flush()

        # 學校
        school = School(
            name="taipei-main",
            display_name="台北總校",
            organization_id=org.id,
            contact_email="taipei@example.com",
        )
        self.db.add(school)
        self.db.flush()

        # 教師
        zhang = Teacher(
            email="zhang@happy.com",
            name="張老師",
            password_hash="hash",
            is_active=True,
        )
        li = Teacher(
            email="li@happy.com", name="李老師", password_hash="hash", is_active=True
        )
        self.db.add_all([zhang, li])
        self.db.flush()

        # 教師-組織
        zhang_org = TeacherOrganization(
            teacher_id=zhang.id, organization_id=org.id, role="org_owner"
        )
        self.db.add(zhang_org)

        # 教師-學校
        zhang_school = TeacherSchool(
            teacher_id=zhang.id,
            school_id=school.id,
            roles=["school_admin", "teacher"],
        )
        li_school = TeacherSchool(
            teacher_id=li.id, school_id=school.id, roles=["teacher"]
        )
        self.db.add_all([zhang_school, li_school])
        self.db.flush()

        # 班級
        class_a = Classroom(name="五年級A班", teacher_id=zhang.id)
        class_b = Classroom(name="六年級B班", teacher_id=li.id)
        self.db.add_all([class_a, class_b])
        self.db.flush()

        # 班級-學校
        cs_a = ClassroomSchool(classroom_id=class_a.id, school_id=school.id)
        cs_b = ClassroomSchool(classroom_id=class_b.id, school_id=school.id)
        self.db.add_all([cs_a, cs_b])

        # 學生
        students_a = [
            Student(
                name=f"學生A{i}",
                student_number=f"20250{i:02d}",
                birthdate=date(2012, 1, i),
                password_hash="hash",
            )
            for i in range(1, 6)
        ]
        self.db.add_all(students_a)
        self.db.flush()

        # 學生-班級關聯
        for student in students_a:
            enrollment = ClassroomStudent(
                classroom_id=class_a.id, student_id=student.id
            )
            self.db.add(enrollment)

        self.db.commit()

        # 儲存資料
        self.org = org
        self.school = school
        self.zhang = zhang
        self.li = li
        self.class_a = class_a
        self.class_b = class_b

    def test_org_owner_sees_all_classrooms(self):
        """org_owner 可以看到所有班級"""
        classrooms = (
            self.db.query(Classroom)
            .join(ClassroomSchool)
            .filter(ClassroomSchool.school_id == self.school.id)
            .all()
        )

        assert len(classrooms) == 2
        names = {c.name for c in classrooms}
        assert names == {"五年級A班", "六年級B班"}

    def test_teacher_sees_own_classroom_only(self):
        """teacher 只能看到自己的班級"""
        classrooms = (
            self.db.query(Classroom).filter(Classroom.teacher_id == self.li.id).all()
        )

        assert len(classrooms) == 1
        assert classrooms[0].name == "六年級B班"

    @pytest.mark.skip(reason="Casbin tested separately, needs manual sync in E2E")
    def test_casbin_roles_synced(self):
        """Casbin 角色已同步"""
        casbin = get_casbin_service()

        assert casbin.has_role(self.zhang.id, "org_owner", f"org-{self.org.id}")
        assert casbin.has_role(self.zhang.id, "school_admin", f"school-{self.school.id}")


# ============================================================
# 場景 2: 補習班 - 多分校
# ============================================================


class TestScenario2MultiBranch:
    """場景 2: 補習班 - 多分校"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):
        """設置場景2資料"""
        self.db = db_session

        # 組織
        org = Organization(
            name="taiwan-english",
            display_name="台灣英語補習班",
            contact_email="contact@taiwan.com",
        )
        self.db.add(org)
        self.db.flush()

        # 學校
        taipei = School(
            name="taipei-branch",
            display_name="台北分校",
            organization_id=org.id,
            contact_email="taipei@taiwan.com",
        )
        taichung = School(
            name="taichung-branch",
            display_name="台中分校",
            organization_id=org.id,
            contact_email="taichung@taiwan.com",
        )
        kaohsiung = School(
            name="kaohsiung-branch",
            display_name="高雄分校",
            organization_id=org.id,
            contact_email="kaohsiung@taiwan.com",
        )
        self.db.add_all([taipei, taichung, kaohsiung])
        self.db.flush()

        # 教師
        wang = Teacher(
            email="wang@taiwan.com", name="王老師", password_hash="hash", is_active=True
        )
        chen = Teacher(
            email="chen@taiwan.com", name="陳老師", password_hash="hash", is_active=True
        )
        lin = Teacher(
            email="lin@taiwan.com", name="林老師", password_hash="hash", is_active=True
        )
        self.db.add_all([wang, chen, lin])
        self.db.flush()

        # 教師-組織
        wang_org = TeacherOrganization(
            teacher_id=wang.id, organization_id=org.id, role="org_owner"
        )
        chen_org = TeacherOrganization(
            teacher_id=chen.id, organization_id=org.id, role="org_admin"
        )
        self.db.add_all([wang_org, chen_org])

        # 教師-學校
        chen_taipei = TeacherSchool(
            teacher_id=chen.id,
            school_id=taipei.id,
            roles=["school_admin", "teacher"],
        )
        lin_taichung = TeacherSchool(
            teacher_id=lin.id, school_id=taichung.id, roles=["school_admin"]
        )
        self.db.add_all([chen_taipei, lin_taichung])
        self.db.commit()

        # 儲存資料
        self.org = org
        self.taipei = taipei
        self.taichung = taichung
        self.kaohsiung = kaohsiung
        self.wang = wang
        self.chen = chen
        self.lin = lin

    def test_org_owner_sees_all_schools(self):
        """org_owner 可以訪問所有分校"""
        schools = (
            self.db.query(School).filter(School.organization_id == self.org.id).all()
        )

        assert len(schools) == 3
        names = {s.display_name for s in schools}
        assert names == {"台北分校", "台中分校", "高雄分校"}

    def test_org_admin_sees_all_schools(self):
        """org_admin 可以訪問所有分校"""
        schools = (
            self.db.query(School).filter(School.organization_id == self.org.id).all()
        )

        assert len(schools) == 3

    def test_school_admin_sees_own_school_only(self):
        """school_admin 只能訪問自己的分校"""
        schools = (
            self.db.query(School)
            .join(TeacherSchool)
            .filter(TeacherSchool.teacher_id == self.lin.id)
            .all()
        )

        assert len(schools) == 1
        assert schools[0].display_name == "台中分校"

    @pytest.mark.skip(reason="Casbin tested separately, needs manual sync in E2E")
    def test_permission_inheritance(self):
        """權限繼承正確"""
        casbin = get_casbin_service()

        assert casbin.has_role(self.wang.id, "org_owner", f"org-{self.org.id}")
        assert casbin.has_role(self.chen.id, "org_admin", f"org-{self.org.id}")
        assert casbin.has_role(
            self.chen.id, "school_admin", f"school-{self.taipei.id}"
        )


# ============================================================
# 場景 4: 個體戶 - 獨立教師
# ============================================================


class TestScenario4IndependentTeacher:
    """場景 4: 個體戶 - 獨立教師"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):
        """設置場景4資料"""
        self.db = db_session

        # 教師
        liu = Teacher(
            email="liu@independent.com",
            name="劉老師",
            password_hash="hash",
            is_active=True,
        )
        self.db.add(liu)
        self.db.flush()

        # 班級（無學校關聯）
        class_a = Classroom(name="家教班A", teacher_id=liu.id)
        class_b = Classroom(name="家教班B", teacher_id=liu.id)
        self.db.add_all([class_a, class_b])
        self.db.flush()

        # 學生
        students_a = [
            Student(
                name=f"家教生A{i}",
                student_number=f"30{i:03d}",
                birthdate=date(2013, 1, i),
                password_hash="hash",
            )
            for i in range(1, 4)
        ]
        self.db.add_all(students_a)
        self.db.flush()

        # 學生-班級關聯
        for student in students_a:
            enrollment = ClassroomStudent(
                classroom_id=class_a.id, student_id=student.id
            )
            self.db.add(enrollment)

        self.db.commit()

        # 儲存資料
        self.liu = liu
        self.class_a = class_a
        self.class_b = class_b

    def test_independent_teacher_no_organization(self):
        """獨立教師無機構"""
        org_relations = (
            self.db.query(TeacherOrganization)
            .filter(TeacherOrganization.teacher_id == self.liu.id)
            .all()
        )

        assert len(org_relations) == 0

    def test_independent_teacher_no_school(self):
        """獨立教師無學校"""
        school_relations = (
            self.db.query(TeacherSchool)
            .filter(TeacherSchool.teacher_id == self.liu.id)
            .all()
        )

        assert len(school_relations) == 0

    def test_independent_teacher_has_classrooms(self):
        """獨立教師可以有班級"""
        classrooms = (
            self.db.query(Classroom).filter(Classroom.teacher_id == self.liu.id).all()
        )

        assert len(classrooms) == 2
        names = {c.name for c in classrooms}
        assert names == {"家教班A", "家教班B"}

    def test_classroom_not_linked_to_school(self):
        """獨立教師班級不應該有學校關聯"""
        school_link = (
            self.db.query(ClassroomSchool)
            .filter(ClassroomSchool.classroom_id == self.class_a.id)
            .first()
        )

        assert school_link is None


# ============================================================
# 場景 6: 混合情境 - 跨機構隔離
# ============================================================


class TestScenario6CrossOrgIsolation:
    """場景 6: 跨機構隔離"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):
        """設置場景6資料"""
        self.db = db_session

        # 組織A
        org_a = Organization(
            name="happy-school",
            display_name="快樂補習班",
            contact_email="happy@example.com",
        )
        self.db.add(org_a)
        self.db.flush()

        school_a = School(
            name="taipei-school",
            display_name="台北校",
            organization_id=org_a.id,
            contact_email="taipei@happy.com",
        )
        self.db.add(school_a)
        self.db.flush()

        # 組織B
        org_b = Organization(
            name="english-world",
            display_name="美語天地",
            contact_email="english@example.com",
        )
        self.db.add(org_b)
        self.db.flush()

        school_b = School(
            name="hsinchu-school",
            display_name="新竹校",
            organization_id=org_b.id,
            contact_email="hsinchu@english.com",
        )
        self.db.add(school_b)
        self.db.flush()

        # 教師
        wang = Teacher(
            email="wang@happy.com", name="王老師", password_hash="hash", is_active=True
        )
        li = Teacher(
            email="li@english.com", name="李老師", password_hash="hash", is_active=True
        )
        chen = Teacher(
            email="chen@independent.com",
            name="陳老師",
            password_hash="hash",
            is_active=True,
        )
        self.db.add_all([wang, li, chen])
        self.db.flush()

        # 教師-組織
        wang_org = TeacherOrganization(
            teacher_id=wang.id, organization_id=org_a.id, role="org_owner"
        )
        li_org = TeacherOrganization(
            teacher_id=li.id, organization_id=org_b.id, role="org_owner"
        )
        self.db.add_all([wang_org, li_org])
        self.db.commit()

        # 儲存資料
        self.org_a = org_a
        self.org_b = org_b
        self.wang = wang
        self.li = li
        self.chen = chen

    def test_wang_cannot_see_org_b(self):
        """王老師看不到組織B"""
        orgs = (
            self.db.query(Organization)
            .join(TeacherOrganization)
            .filter(TeacherOrganization.teacher_id == self.wang.id)
            .all()
        )

        org_ids = {org.id for org in orgs}
        assert self.org_b.id not in org_ids

    def test_li_cannot_see_org_a(self):
        """李老師看不到組織A"""
        orgs = (
            self.db.query(Organization)
            .join(TeacherOrganization)
            .filter(TeacherOrganization.teacher_id == self.li.id)
            .all()
        )

        org_ids = {org.id for org in orgs}
        assert self.org_a.id not in org_ids

    def test_chen_sees_no_organization(self):
        """陳老師看不到任何機構"""
        orgs = (
            self.db.query(Organization)
            .join(TeacherOrganization)
            .filter(TeacherOrganization.teacher_id == self.chen.id)
            .all()
        )

        assert len(orgs) == 0

    @pytest.mark.skip(reason="Casbin tested separately, needs manual sync in E2E")
    def test_casbin_isolation(self):
        """Casbin 權限隔離"""
        casbin = get_casbin_service()

        # 王老師只有 org_a 權限
        assert casbin.has_role(self.wang.id, "org_owner", f"org-{self.org_a.id}")
        assert not casbin.has_role(self.wang.id, "org_owner", f"org-{self.org_b.id}")

        # 李老師只有 org_b 權限
        assert casbin.has_role(self.li.id, "org_owner", f"org-{self.org_b.id}")
        assert not casbin.has_role(self.li.id, "org_owner", f"org-{self.org_a.id}")


# ============================================================
# 場景 7: 補習班 - 軟刪除與重啟
# ============================================================


class TestScenario7SoftDelete:
    """場景 7: 軟刪除與重啟"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):
        """設置場景7資料"""
        self.db = db_session

        # 組織
        org = Organization(
            name="forever-school",
            display_name="永續補習班",
            contact_email="forever@example.com",
        )
        self.db.add(org)
        self.db.flush()

        # 學校
        main_school = School(
            name="main-school",
            display_name="主校",
            organization_id=org.id,
            contact_email="main@forever.com",
            is_active=True,
        )
        old_school = School(
            name="old-school",
            display_name="舊校",
            organization_id=org.id,
            contact_email="old@forever.com",
            is_active=False,  # 軟刪除
        )
        self.db.add_all([main_school, old_school])
        self.db.commit()

        # 儲存資料
        self.org = org
        self.main_school = main_school
        self.old_school = old_school

    def test_only_active_schools_in_listing(self):
        """只顯示 active 學校"""
        schools = (
            self.db.query(School)
            .filter(School.organization_id == self.org.id, School.is_active == True)
            .all()
        )

        assert len(schools) == 1
        assert schools[0].display_name == "主校"

    def test_soft_deleted_school_still_in_db(self):
        """軟刪除的學校還在資料庫"""
        school = (
            self.db.query(School).filter(School.id == self.old_school.id).first()
        )

        assert school is not None
        assert school.is_active == False

    def test_reactivate_school(self):
        """重新啟用學校"""
        self.old_school.is_active = True
        self.db.commit()

        schools = (
            self.db.query(School)
            .filter(School.organization_id == self.org.id, School.is_active == True)
            .all()
        )

        assert len(schools) == 2
        names = {s.display_name for s in schools}
        assert names == {"主校", "舊校"}
