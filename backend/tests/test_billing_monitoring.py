"""測試帳單監控系統

測試範圍：
1. Email 服務 - 每日帳單摘要郵件
2. AI 分析服務 - 異常檢測和趨勢分析
3. 每日報告腳本 - 端到端測試

執行方式:
    pytest tests/test_billing_monitoring.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# 添加 backend 目錄到 Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from services.email_service import EmailService  # noqa: E402
from services.billing_analysis_service import (  # noqa: E402
    BillingAnalysisService,
)


class TestEmailBillingReport:
    """測試 Email 服務的帳單報告功能"""

    def setup_method(self):
        """測試前置設定"""
        self.email_service = EmailService()

    def test_send_billing_daily_summary_basic(self):
        """測試基本的每日摘要郵件發送"""
        # 準備測試數據
        billing_data = {
            "total_cost": 123.45,
            "period": {"start": "2025-11-23", "end": "2025-11-30"},
            "top_services": [
                {"service": "Cloud Run", "cost": 50.0},
                {"service": "Cloud Storage", "cost": 30.0},
                {"service": "Artifact Registry", "cost": 20.0},
            ],
            "daily_costs": [
                {"date": "2025-11-24", "cost": 15.5},
                {"date": "2025-11-25", "cost": 18.2},
                {"date": "2025-11-26", "cost": 17.8},
                {"date": "2025-11-27", "cost": 19.1},
                {"date": "2025-11-28", "cost": 20.3},
                {"date": "2025-11-29", "cost": 16.9},
                {"date": "2025-11-30", "cost": 15.6},
            ],
        }

        analysis = {
            "has_anomalies": False,
            "anomalies": [],
            "summary": "系統運作正常，費用在合理範圍內。",
            "recommendations": ["✅ 系統運作正常，費用在合理範圍內"],
            "trend": "穩定",
            "trend_percent": 2.5,
        }

        # 執行測試（開發模式，不實際發送郵件）
        result = self.email_service.send_billing_daily_summary(
            admin_email="test@example.com",
            admin_name="Test Admin",
            billing_data=billing_data,
            analysis=analysis,
        )

        # 驗證結果
        assert result is True, "Email should be sent successfully in dev mode"

    def test_send_billing_summary_with_anomalies(self):
        """測試包含異常的帳單摘要郵件"""
        billing_data = {
            "total_cost": 250.0,
            "period": {"start": "2025-11-23", "end": "2025-11-30"},
            "top_services": [
                {"service": "Cloud Storage", "cost": 150.0},  # 異常增長
                {"service": "Cloud Run", "cost": 60.0},
                {"service": "Artifact Registry", "cost": 40.0},
            ],
            "daily_costs": [
                {"date": "2025-11-24", "cost": 20.0},
                {"date": "2025-11-25", "cost": 25.0},
                {"date": "2025-11-26", "cost": 30.0},
                {"date": "2025-11-27", "cost": 35.0},
                {"date": "2025-11-28", "cost": 40.0},
                {"date": "2025-11-29", "cost": 50.0},
                {"date": "2025-11-30", "cost": 50.0},
            ],
        }

        analysis = {
            "has_anomalies": True,
            "anomalies": [
                {
                    "service": "Cloud Storage",
                    "current_cost": 150.0,
                    "previous_cost": 20.0,
                    "increase_percent": 650.0,
                }
            ],
            "summary": "⚠️ Cloud Storage 費用異常增長 650%，建議立即檢查。",
            "recommendations": [
                "⚠️ Cloud Storage 費用異常增長 650.0%，建議立即檢查使用量和配置",
                "💡 Cloud Storage 費用較高 ($150.00)，建議檢查 Lifecycle Policy 和冷儲存選項",
            ],
            "trend": "上升",
            "trend_percent": 150.0,
        }

        result = self.email_service.send_billing_daily_summary(
            admin_email="test@example.com",
            admin_name="Test Admin",
            billing_data=billing_data,
            analysis=analysis,
        )

        assert result is True

    def test_generate_trend_chart_html(self):
        """測試趨勢圖表 HTML 生成"""
        daily_costs = [
            {"date": "2025-11-24", "cost": 10.0},
            {"date": "2025-11-25", "cost": 15.0},
            {"date": "2025-11-26", "cost": 20.0},
            {"date": "2025-11-27", "cost": 25.0},
            {"date": "2025-11-28", "cost": 20.0},
            {"date": "2025-11-29", "cost": 18.0},
            {"date": "2025-11-30", "cost": 22.0},
        ]

        chart_html = self.email_service._generate_trend_chart_html(daily_costs)

        # 驗證 HTML 包含所有日期
        for item in daily_costs:
            assert item["date"] in chart_html
            assert f"${item['cost']:.2f}" in chart_html

        # 驗證 HTML 結構
        assert "<div" in chart_html
        assert "background" in chart_html

    def test_generate_trend_chart_empty_data(self):
        """測試空數據的趨勢圖表"""
        chart_html = self.email_service._generate_trend_chart_html([])
        assert "暫無數據" in chart_html

    def test_generate_trend_chart_zero_costs(self):
        """測試全為零的費用數據"""
        daily_costs = [
            {"date": "2025-11-24", "cost": 0.0},
            {"date": "2025-11-25", "cost": 0.0},
        ]

        chart_html = self.email_service._generate_trend_chart_html(daily_costs)
        assert "$0.00" in chart_html


class TestBillingAnalysisService:
    """測試帳單 AI 分析服務"""

    def setup_method(self):
        """測試前置設定"""
        self.analysis_service = BillingAnalysisService()

    @pytest.mark.asyncio
    async def test_analyze_billing_data_normal(self):
        """測試正常情況的帳單分析"""
        current_data = {
            "total_cost": 100.0,
            "top_services": [
                {"service": "Cloud Run", "cost": 50.0},
                {"service": "Cloud Storage", "cost": 30.0},
                {"service": "Artifact Registry", "cost": 20.0},
            ],
        }

        previous_data = {
            "total_cost": 190.0,  # 包含當前期間的 100 + 前期的 90
            "top_services": [
                {"service": "Cloud Run", "cost": 95.0},
                {"service": "Cloud Storage", "cost": 55.0},
                {"service": "Artifact Registry", "cost": 40.0},
            ],
        }

        anomaly_data = {"has_anomaly": False, "anomalies": []}

        result = await self.analysis_service.analyze_billing_data(
            current_data, previous_data, anomaly_data
        )

        # 驗證結果結構
        assert "has_anomalies" in result
        assert "summary" in result
        assert "recommendations" in result
        assert "trend" in result
        assert "cost_attribution" in result

        # 驗證無異常
        assert result["has_anomalies"] is False
        assert result["trend"] in ["上升", "下降", "穩定"]

    @pytest.mark.asyncio
    async def test_analyze_billing_data_with_anomaly(self):
        """測試有異常的帳單分析"""
        current_data = {
            "total_cost": 200.0,
            "top_services": [
                {"service": "Cloud Storage", "cost": 150.0},  # 異常
                {"service": "Cloud Run", "cost": 30.0},
                {"service": "Artifact Registry", "cost": 20.0},
            ],
        }

        previous_data = {
            "total_cost": 250.0,  # 前期總計 50
            "top_services": [
                {"service": "Cloud Storage", "cost": 170.0},
                {"service": "Cloud Run", "cost": 50.0},
                {"service": "Artifact Registry", "cost": 30.0},
            ],
        }

        anomaly_data = {
            "has_anomaly": True,
            "anomalies": [
                {
                    "service": "Cloud Storage",
                    "current_cost": 150.0,
                    "previous_cost": 20.0,
                    "increase_percent": 650.0,
                }
            ],
        }

        result = await self.analysis_service.analyze_billing_data(
            current_data, previous_data, anomaly_data
        )

        # 驗證異常被正確識別
        assert result["has_anomalies"] is True
        assert len(result["anomalies"]) > 0
        assert result["anomalies"][0]["service"] == "Cloud Storage"

        # 驗證有建議
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_cost_attribution_analysis(self):
        """測試成本歸因分析"""
        billing_data = {
            "total_cost": 100.0,
            "top_services": [
                {"service": "Cloud Run", "cost": 60.0},  # 60%
                {"service": "Cloud Storage", "cost": 25.0},  # 25%
                {"service": "Artifact Registry", "cost": 15.0},  # 15%
            ],
        }

        attribution = self.analysis_service._analyze_cost_attribution(billing_data)

        # 驗證主要驅動因素
        assert "main_drivers" in attribution
        assert len(attribution["main_drivers"]) == 3
        assert attribution["main_drivers"][0]["service"] == "Cloud Run"
        assert attribution["main_drivers"][0]["percentage"] == 60.0

        # 驗證 Top 3 佔比
        assert "top_percentage" in attribution
        assert attribution["top_percentage"] == 100.0

    def test_generate_basic_recommendations_no_anomaly(self):
        """測試無異常時的建議生成"""
        billing_data = {
            "top_services": [
                {"service": "Cloud Run", "cost": 50.0},
                {"service": "Cloud Storage", "cost": 30.0},
            ],
        }

        recommendations = self.analysis_service._generate_basic_recommendations(
            billing_data, [], "穩定"
        )

        # 應該有建議
        assert len(recommendations) > 0
        # 應該包含正常訊息
        assert any("Cloud Run" in rec for rec in recommendations)

    def test_generate_basic_recommendations_with_anomaly(self):
        """測試有異常時的建議生成"""
        billing_data = {
            "top_services": [{"service": "Cloud Storage", "cost": 150.0}],
        }

        anomalies = [
            {
                "service": "Cloud Storage",
                "current_cost": 150.0,
                "previous_cost": 20.0,
                "increase_percent": 650.0,
            }
        ]

        recommendations = self.analysis_service._generate_basic_recommendations(
            billing_data, anomalies, "上升"
        )

        # 應該有警告建議
        assert len(recommendations) > 0
        assert any("異常" in rec or "Cloud Storage" in rec for rec in recommendations)

    def test_generate_basic_summary(self):
        """測試基礎摘要生成"""
        summary = self.analysis_service._generate_basic_summary(
            current_cost=100.0,
            previous_cost=90.0,
            trend="上升",
            trend_percent=11.1,
            has_anomalies=False,
        )

        # 驗證摘要內容
        assert "100.00" in summary
        assert "上升" in summary or "增加" in summary
        assert "正常" in summary

    def test_generate_basic_summary_with_anomaly(self):
        """測試有異常的摘要生成"""
        summary = self.analysis_service._generate_basic_summary(
            current_cost=200.0,
            previous_cost=50.0,
            trend="上升",
            trend_percent=300.0,
            has_anomalies=True,
        )

        # 應該包含異常警告
        assert "異常" in summary


class TestDailyBillingReport:
    """測試每日報告腳本的核心邏輯"""

    @pytest.mark.asyncio
    async def test_anomaly_check_no_anomaly(self):
        """測試無異常的檢測"""
        # Mock billing service
        mock_service = Mock()
        mock_service.get_billing_summary = AsyncMock(
            side_effect=[
                # Current period
                {
                    "total_cost": 100.0,
                    "data_available": True,
                    "top_services": [{"service": "Cloud Run", "cost": 60.0}],
                },
                # Previous period
                {
                    "total_cost": 190.0,
                    "data_available": True,
                    "top_services": [{"service": "Cloud Run", "cost": 105.0}],
                },
            ]
        )

        # Import and test the function
        from scripts.daily_billing_report import _check_anomalies

        result = await _check_anomalies(mock_service, threshold=50.0)

        assert result["has_anomaly"] is False
        assert result["data_available"] is True

    @pytest.mark.asyncio
    async def test_anomaly_check_with_anomaly(self):
        """測試有異常的檢測"""
        mock_service = Mock()
        mock_service.get_billing_summary = AsyncMock(
            side_effect=[
                # Current period: 費用 200
                {
                    "total_cost": 200.0,
                    "data_available": True,
                    "top_services": [
                        {"service": "Cloud Storage", "cost": 180.0},
                        {"service": "Cloud Run", "cost": 20.0},
                    ],
                },
                # Previous period: 總費用 250（= 當前 200 + 前期 50）
                {
                    "total_cost": 250.0,
                    "data_available": True,
                    "top_services": [
                        {"service": "Cloud Storage", "cost": 190.0},  # = 當前 180 + 前期 10
                        {"service": "Cloud Run", "cost": 60.0},  # = 當前 20 + 前期 40
                    ],
                },
            ]
        )

        from scripts.daily_billing_report import _check_anomalies

        result = await _check_anomalies(mock_service, threshold=50.0)

        # 驗證整體異常（200 vs 50 = 300% 增長，超過 50% 閾值）
        assert result["has_anomaly"] is True
        # 驗證數據可用
        assert result["data_available"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
