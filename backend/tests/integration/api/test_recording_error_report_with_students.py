"""
測試錄音錯誤報告 - 包含學生名單
"""
import pytest
from google.cloud import bigquery
import os


@pytest.mark.skipif(not os.getenv("GCP_PROJECT_ID"), reason="需要 GCP_PROJECT_ID 環境變數")
def test_query_students_with_errors():
    """測試查詢有錯誤的學生名單（兩步驟：BigQuery + PostgreSQL）"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models import Student

    # Step 1: 從 BigQuery 取得有錯誤的 student_ids
    client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))

    query_student_ids = f"""
    SELECT
        student_id,
        COUNT(*) as error_count,
        STRING_AGG(DISTINCT error_type ORDER BY error_type LIMIT 5) as error_types
    FROM `{os.getenv("GCP_PROJECT_ID")}.duotopia_logs.audio_playback_errors`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        AND student_id IS NOT NULL
    GROUP BY student_id
    ORDER BY error_count DESC
    LIMIT 100
    """

    student_errors = list(client.query(query_student_ids).result())

    # Step 2: 從 PostgreSQL 查詢學生資料
    students_with_errors = []
    if student_errors:
        engine = create_engine(os.getenv("DATABASE_URL"))
        SessionLocal = sessionmaker(bind=engine)
        db_session = SessionLocal()

        try:
            student_ids = [row.student_id for row in student_errors]
            students = (
                db_session.query(Student).filter(Student.id.in_(student_ids)).all()
            )

            student_map = {s.id: s for s in students}

            for error_row in student_errors:
                student = student_map.get(error_row.student_id)
                students_with_errors.append(
                    {
                        "student_id": error_row.student_id,
                        "student_name": student.name if student else "（未找到）",
                        "student_email": student.email if student else "（無 Email）",
                        "error_count": error_row.error_count,
                        "error_types": error_row.error_types,
                    }
                )
        finally:
            db_session.close()

    print(f"\n找到 {len(students_with_errors)} 位有錯誤的學生：")
    for student in students_with_errors[:10]:  # 只顯示前 10 位
        print(
            f"  - {student['student_name']} (ID {student['student_id']}) ({student['student_email']}): "
            f"{student['error_count']} 次錯誤"
        )
        print(f"    錯誤類型: {student['error_types']}")

    # 驗證查詢格式正確
    if students_with_errors:
        assert "student_id" in students_with_errors[0]
        assert "student_name" in students_with_errors[0]
        assert "student_email" in students_with_errors[0]
        assert "error_count" in students_with_errors[0]
        assert "error_types" in students_with_errors[0]


@pytest.mark.skipif(not os.getenv("CRON_SECRET"), reason="需要 CRON_SECRET 環境變數")
def test_recording_error_report_endpoint(test_client):
    """測試錄音錯誤報告 API 端點（整合測試）"""
    import os

    response = test_client.post(
        "/api/cron/recording-error-report",
        headers={"X-Cron-Secret": os.getenv("CRON_SECRET", "dev-secret-change-me")},
    )

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    print(f"\n報告狀態: {data['status']}")

    if "students_with_errors" in data:
        print(f"有錯誤的學生數: {data['students_with_errors']}")


if __name__ == "__main__":
    # 可以直接執行測試
    print("測試錄音錯誤報告 - 學生名單查詢\n")
    test_query_students_with_errors()
