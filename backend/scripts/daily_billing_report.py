"""每日帳單報告生成腳本

此腳本會：
1. 調用 billing_service 獲取過去 7 天的帳單數據
2. 調用 billing_analysis_service 進行 AI 分析
3. 發送郵件給管理員
4. 可選：保存歷史數據到文件或數據庫

執行方式:
    python scripts/daily_billing_report.py

環境變數:
    ADMIN_EMAIL: 接收報告的管理員 Email（必填）
    ADMIN_NAME: 管理員姓名（選填，默認 "Admin"）
    SMTP_USER: SMTP 用戶名（必填）
    SMTP_PASSWORD: SMTP 密碼（必填）
    ANOMALY_THRESHOLD: 異常閾值百分比（選填，默認 50）
    SAVE_HISTORY: 是否保存歷史數據（選填，默認 true）
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# 添加 backend 目錄到 Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from services.billing_service import get_billing_service
from services.billing_analysis_service import get_billing_analysis_service
from services.email_service import email_service

# 創建 logs 目錄（如果不存在）
logs_dir = backend_dir / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(logs_dir / "billing_report.log"),
    ],
)
logger = logging.getLogger(__name__)


async def generate_and_send_daily_report():
    """生成並發送每日帳單報告"""
    try:
        # 1. 讀取環境變數
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_name = os.getenv("ADMIN_NAME", "Admin")
        anomaly_threshold = float(os.getenv("ANOMALY_THRESHOLD", "50"))
        save_history = os.getenv("SAVE_HISTORY", "true").lower() == "true"

        if not admin_email:
            logger.error("❌ ADMIN_EMAIL 環境變數未設定")
            return False

        logger.info(f"📊 開始生成每日帳單報告 - {datetime.now()}")

        # 2. 獲取 billing service
        billing_service = get_billing_service()
        analysis_service = get_billing_analysis_service()

        # 3. 查詢當前期間數據（過去 7 天）
        logger.info("📈 查詢過去 7 天帳單數據...")
        current_data = await billing_service.get_billing_summary(days=7)

        if not current_data.get("data_available"):
            logger.warning("⚠️ BigQuery 數據尚未可用，跳過此次報告")
            return False

        # 4. 查詢前期數據（過去 14 天，用於比較）
        logger.info("📊 查詢前期數據（用於趨勢分析）...")
        previous_data = await billing_service.get_billing_summary(days=14)

        # 5. 執行異常檢測
        logger.info(f"🔍 執行異常檢測（閾值: {anomaly_threshold}%）...")
        anomaly_data = await _check_anomalies(
            billing_service, threshold=anomaly_threshold
        )

        # 6. AI 分析
        logger.info("🤖 執行 AI 分析...")
        analysis = await analysis_service.analyze_billing_data(
            current_data, previous_data, anomaly_data
        )

        # 7. 保存歷史數據（可選）
        if save_history:
            logger.info("💾 保存歷史數據...")
            await _save_history(current_data, analysis)

        # 8. 發送郵件
        logger.info(f"📧 發送報告到 {admin_email}...")
        success = email_service.send_billing_daily_summary(
            admin_email=admin_email,
            admin_name=admin_name,
            billing_data=current_data,
            analysis=analysis,
        )

        if success:
            logger.info("✅ 每日帳單報告發送成功")
            print(f"\n✅ 報告已發送到: {admin_email}")
            print(f"📊 總費用: ${current_data.get('total_cost', 0):.2f}")
            print(f"📈 趨勢: {analysis.get('trend', 'Unknown')}")
            if analysis.get("has_anomalies"):
                print(f"⚠️ 異常數量: {len(analysis.get('anomalies', []))}")
        else:
            logger.error("❌ 郵件發送失敗")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ 生成報告失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


async def _check_anomalies(billing_service, threshold: float = 50.0) -> dict:
    """檢查帳單異常"""
    try:
        # 查詢當前期間和前期
        current = await billing_service.get_billing_summary(days=7)
        previous = await billing_service.get_billing_summary(days=14)

        if not current.get("data_available") or not previous.get("data_available"):
            return {"has_anomaly": False, "anomalies": [], "data_available": False}

        current_cost = current.get("total_cost", 0)
        total_cost = previous.get("total_cost", 0)
        previous_cost = total_cost - current_cost

        # 計算增長百分比
        if previous_cost == 0:
            increase_percent = 100.0 if current_cost > 0 else 0.0
        else:
            increase_percent = ((current_cost - previous_cost) / previous_cost) * 100

        has_anomaly = increase_percent > threshold

        # 檢查各服務的異常
        anomalies = []
        current_services = {
            s["service"]: s["cost"] for s in current.get("top_services", [])
        }
        previous_services = {
            s["service"]: s["cost"] for s in previous.get("top_services", [])
        }

        for service, current_service_cost in current_services.items():
            previous_service_cost = previous_services.get(service, 0)

            if previous_service_cost == 0:
                service_increase = 100.0 if current_service_cost > 0 else 0.0
            else:
                service_increase = (
                    (current_service_cost - previous_service_cost)
                    / previous_service_cost
                ) * 100

            if service_increase > threshold:
                anomalies.append(
                    {
                        "service": service,
                        "current_cost": round(current_service_cost, 2),
                        "previous_cost": round(previous_service_cost, 2),
                        "increase_percent": round(service_increase, 2),
                    }
                )

        return {
            "has_anomaly": has_anomaly,
            "anomalies": sorted(
                anomalies, key=lambda x: x["increase_percent"], reverse=True
            ),
            "data_available": True,
        }

    except Exception as e:
        logger.error(f"❌ Anomaly check failed: {e}")
        return {"has_anomaly": False, "anomalies": [], "data_available": False}


async def _save_history(billing_data: dict, analysis: dict):
    """保存歷史數據到 JSON 文件"""
    try:
        # 創建 history 目錄
        history_dir = backend_dir / "data" / "billing_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名（按日期）
        today = datetime.now().strftime("%Y-%m-%d")
        filename = history_dir / f"billing_{today}.json"

        # 組合數據
        history_data = {
            "date": today,
            "timestamp": datetime.now().isoformat(),
            "billing_data": billing_data,
            "analysis": analysis,
        }

        # 寫入文件
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 歷史數據已保存: {filename}")

    except Exception as e:
        logger.error(f"❌ 保存歷史數據失敗: {e}")


def main():
    """主函數"""
    print("=" * 60)
    print("📊 Duotopia 每日帳單報告生成器")
    print("=" * 60)
    print()

    # 檢查必要環境變數
    if not os.getenv("ADMIN_EMAIL"):
        print("❌ 錯誤: 請設定 ADMIN_EMAIL 環境變數")
        print("   export ADMIN_EMAIL=your-email@example.com")
        sys.exit(1)

    if not os.getenv("SMTP_USER") or not os.getenv("SMTP_PASSWORD"):
        print("⚠️ 警告: SMTP 未設定，將使用開發模式（僅記錄日誌）")
        print()

    # 執行報告生成
    success = asyncio.run(generate_and_send_daily_report())

    print()
    print("=" * 60)
    if success:
        print("✅ 完成")
        sys.exit(0)
    else:
        print("❌ 失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()
