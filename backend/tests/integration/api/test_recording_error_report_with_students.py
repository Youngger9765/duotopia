"""
測試錄音錯誤報告 - 包含學生名單
"""
import pytest
from google.cloud import bigquery
import os


@pytest.mark.skipif(not os.getenv("GCP_PROJECT_ID"), reason="需要 GCP_PROJECT_ID 環境變數")
def test_query_students_with_errors():
    """測試查詢有錯誤的學生名單"""
    client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))

    query = f"""
    SELECT DISTINCT
        e.student_id,
        s.name as student_name,
        s.email as student_email,
        COUNT(*) as error_count,
        STRING_AGG(DISTINCT e.error_type ORDER BY e.error_type LIMIT 5) as error_types
    FROM `{os.getenv("GCP_PROJECT_ID")}.duotopia_logs.audio_playback_errors` e
    LEFT JOIN `{os.getenv("GCP_PROJECT_ID")}.duotopia.students` s
        ON e.student_id = s.id
    WHERE e.timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        AND e.student_id IS NOT NULL
    GROUP BY e.student_id, s.name, s.email
    ORDER BY error_count DESC
    LIMIT 10
    """

    results = list(client.query(query).result())

    print(f"\n找到 {len(results)} 位有錯誤的學生：")
    for row in results:
        print(
            f"  - {row.student_name or f'ID {row.student_id}'} ({row.student_email or 'no email'}): "
            f"{row.error_count} 次錯誤"
        )
        print(f"    錯誤類型: {row.error_types}")

    # 驗證查詢格式正確
    if results:
        assert hasattr(results[0], "student_id")
        assert hasattr(results[0], "student_name")
        assert hasattr(results[0], "student_email")
        assert hasattr(results[0], "error_count")
        assert hasattr(results[0], "error_types")


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
