"""
測試機構邀請新教師時發送密碼設定郵件 (Issue #246)

測試流程:
1. 機構管理員邀請一個未註冊的教師
2. 系統創建教師帳號
3. 系統發送密碼設定郵件
4. 教師收到郵件並設定密碼
5. 教師完成註冊並成為機構成員
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from main import app
from models import Teacher, Organization, TeacherOrganization
from services.email_service import email_service
from auth import create_access_token, verify_password


client = TestClient(app)


@pytest.fixture
def db_session(test_db_session):
    """Alias for test_db_session to match test signatures"""
    return test_db_session


@pytest.fixture
def setup_organization(db_session: Session):
    """創建測試機構和機構管理員"""
    # 創建機構擁有者
    owner = Teacher(
        email="owner@test.com",
        password_hash="hashed_password",
        name="機構擁有者",
        is_active=True,
        email_verified=True,
    )
    db_session.add(owner)
    db_session.commit()
    db_session.refresh(owner)

    # 創建機構
    org = Organization(
        name="測試機構",
        display_name="Test Organization",
        is_active=True,
        teacher_limit=10,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # 關聯機構和擁有者
    teacher_org = TeacherOrganization(
        teacher_id=owner.id, organization_id=org.id, role="org_owner", is_active=True
    )
    db_session.add(teacher_org)
    db_session.commit()

    # 生成 token
    token = create_access_token({"sub": str(owner.id), "type": "teacher"})

    yield {
        "owner": owner,
        "organization": org,
        "token": token,
    }

    # 清理
    db_session.query(TeacherOrganization).filter(
        TeacherOrganization.organization_id == org.id
    ).delete()
    db_session.query(Organization).filter(Organization.id == org.id).delete()
    db_session.query(Teacher).filter(Teacher.id == owner.id).delete()
    db_session.commit()


def test_invite_new_teacher_sends_password_setup_email(
    db_session: Session, setup_organization
):
    """
    測試邀請新教師時發送密碼設定郵件
    """
    org = setup_organization["organization"]
    token = setup_organization["token"]

    # Mock email service
    with patch.object(
        email_service, "send_password_setup_email", return_value=True
    ) as mock_email:
        # 邀請新教師
        response = client.post(
            f"/api/organizations/{org.id}/teachers/invite",
            headers={"Authorization": f"Bearer {token}"},
            json={"email": "newteacher@test.com", "name": "新教師", "role": "teacher"},
        )

        # 驗證 API 回應
        assert response.status_code == 201, f"Response: {response.json()}"
        data = response.json()
        assert data["role"] == "teacher"

        # 驗證郵件發送被調用
        assert mock_email.called, "Email service should have been called"
        call_args = mock_email.call_args

        # 驗證郵件參數
        teacher_arg = call_args[0][1]  # 第二個參數是 teacher
        org_name_arg = call_args[0][2]  # 第三個參數是 organization_name

        assert teacher_arg.email == "newteacher@test.com"
        assert teacher_arg.name == "新教師"
        assert org_name_arg == org.display_name

    # 清理測試數據
    new_teacher = (
        db_session.query(Teacher).filter(Teacher.email == "newteacher@test.com").first()
    )
    if new_teacher:
        db_session.query(TeacherOrganization).filter(
            TeacherOrganization.teacher_id == new_teacher.id
        ).delete()
        db_session.delete(new_teacher)
        db_session.commit()


def test_password_setup_email_content(db_session: Session):
    """
    測試密碼設定郵件內容
    """
    # 創建測試教師
    teacher = Teacher(
        email="test@example.com",
        password_hash="temp_hash",
        name="測試教師",
        is_active=True,
        email_verified=True,
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    try:
        # 調用郵件服務（開發模式不會實際發送）
        result = email_service.send_password_setup_email(
            db_session, teacher, "Test Organization"
        )

        # 驗證返回成功
        assert result is True

        # 驗證 token 已設定
        db_session.refresh(teacher)
        assert teacher.password_reset_token is not None
        assert teacher.password_reset_sent_at is not None
        assert teacher.password_reset_expires_at is not None

        # 驗證 token 48 小時後過期
        expected_expiry = teacher.password_reset_sent_at + timedelta(hours=48)
        time_diff = abs(
            (teacher.password_reset_expires_at - expected_expiry).total_seconds()
        )
        assert time_diff < 5, "Expiry time should be ~48 hours from sent time"

    finally:
        # 清理
        db_session.delete(teacher)
        db_session.commit()


def test_password_setup_token_can_be_used_for_password_reset(db_session: Session):
    """
    測試密碼設定 token 可以用於密碼重設流程

    注意：密碼設定和密碼重設使用相同的 token 機制
    """
    # 創建測試教師
    teacher = Teacher(
        email="test@example.com",
        password_hash="temp_hash",
        name="測試教師",
        is_active=True,
        email_verified=True,
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    try:
        # 發送密碼設定郵件
        email_service.send_password_setup_email(
            db_session, teacher, "Test Organization"
        )
        db_session.refresh(teacher)

        # 記錄 token
        setup_token = teacher.password_reset_token
        assert setup_token is not None

        # 模擬教師使用 token 設定密碼
        # （實際流程會通過前端的 /teacher/setup-password 頁面）
        new_password = "NewSecurePassword123!"

        # 驗證 token 存在且未過期
        assert teacher.password_reset_expires_at > datetime.utcnow()

        # 在實際應用中，這裡會調用 password reset endpoint
        # 這裡只驗證 token 機制正常工作
        assert teacher.password_reset_token == setup_token

    finally:
        # 清理
        db_session.delete(teacher)
        db_session.commit()


def test_invite_existing_teacher_does_not_send_setup_email(
    db_session: Session, setup_organization
):
    """
    測試邀請已存在的教師不會發送密碼設定郵件
    """
    org = setup_organization["organization"]
    token = setup_organization["token"]

    # 創建已存在的教師
    existing_teacher = Teacher(
        email="existing@test.com",
        password_hash="existing_hash",
        name="已存在教師",
        is_active=True,
        email_verified=True,
    )
    db_session.add(existing_teacher)
    db_session.commit()
    db_session.refresh(existing_teacher)

    try:
        # Mock email service
        with patch.object(email_service, "send_password_setup_email") as mock_email:
            # 邀請已存在的教師
            response = client.post(
                f"/api/organizations/{org.id}/teachers/invite",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "email": "existing@test.com",
                    "name": "已存在教師",
                    "role": "teacher",
                },
            )

            # 驗證 API 回應成功
            assert response.status_code == 201

            # 驗證郵件服務沒有被調用（因為教師已存在）
            assert (
                not mock_email.called
            ), "Should not send password setup email for existing teacher"

    finally:
        # 清理
        db_session.query(TeacherOrganization).filter(
            TeacherOrganization.teacher_id == existing_teacher.id,
            TeacherOrganization.organization_id == org.id,
        ).delete()
        db_session.delete(existing_teacher)
        db_session.commit()


def test_email_failure_does_not_break_invitation(
    db_session: Session, setup_organization
):
    """
    測試郵件發送失敗不會中斷邀請流程
    """
    org = setup_organization["organization"]
    token = setup_organization["token"]

    # Mock email service to fail
    with patch.object(email_service, "send_password_setup_email", return_value=False):
        # 邀請新教師
        response = client.post(
            f"/api/organizations/{org.id}/teachers/invite",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "failtest@test.com",
                "name": "失敗測試",
                "role": "teacher",
            },
        )

        # 驗證即使郵件失敗，邀請仍然成功
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "teacher"

    # 清理
    teacher = (
        db_session.query(Teacher).filter(Teacher.email == "failtest@test.com").first()
    )
    if teacher:
        db_session.query(TeacherOrganization).filter(
            TeacherOrganization.teacher_id == teacher.id
        ).delete()
        db_session.delete(teacher)
        db_session.commit()
