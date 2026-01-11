"""GCP Billing AI 分析服務"""
import os
import logging
from typing import Dict, Any, List
from openai import AsyncOpenAI
from utils.http_client import get_http_client

logger = logging.getLogger(__name__)


class BillingAnalysisService:
    """帳單 AI 分析服務"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.use_ai = bool(self.openai_api_key)
        if self.use_ai:
            # Use shared http_client for connection pooling
            self.client = AsyncOpenAI(
                api_key=self.openai_api_key, http_client=get_http_client()
            )
        else:
            self.client = None

    async def analyze_billing_data(
        self,
        current_data: Dict[str, Any],
        previous_data: Dict[str, Any],
        anomaly_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        分析帳單數據並生成報告

        Args:
            current_data: 當前期間數據（7天）
            previous_data: 前期數據（14天）
            anomaly_data: 異常檢測結果

        Returns:
            {
                "has_anomalies": bool,
                "anomalies": [...],
                "summary": str,  # AI 生成的分析摘要
                "recommendations": [str],  # 優化建議
                "trend": str,  # "上升" | "下降" | "穩定"
                "cost_attribution": {...}  # 成本歸因分析
            }
        """
        try:
            # 計算趨勢
            current_cost = current_data.get("total_cost", 0)
            previous_cost = previous_data.get("total_cost", 0) - current_cost

            if previous_cost == 0:
                trend = "穩定" if current_cost == 0 else "上升"
                trend_percent = 0
            else:
                trend_percent = ((current_cost - previous_cost) / previous_cost) * 100
                if trend_percent > 10:
                    trend = "上升"
                elif trend_percent < -10:
                    trend = "下降"
                else:
                    trend = "穩定"

            # 成本歸因分析
            cost_attribution = self._analyze_cost_attribution(current_data)

            # 檢查異常
            has_anomalies = anomaly_data.get("has_anomaly", False)
            anomalies = anomaly_data.get("anomalies", [])

            # 生成基礎建議（不使用 AI）
            recommendations = self._generate_basic_recommendations(
                current_data, anomalies, trend
            )

            # 生成摘要
            if self.use_ai:
                summary = await self._generate_ai_summary(
                    current_data, previous_data, anomalies, trend, trend_percent
                )
            else:
                summary = self._generate_basic_summary(
                    current_cost, previous_cost, trend, trend_percent, has_anomalies
                )

            return {
                "has_anomalies": has_anomalies,
                "anomalies": anomalies,
                "summary": summary,
                "recommendations": recommendations,
                "trend": trend,
                "trend_percent": round(trend_percent, 2),
                "cost_attribution": cost_attribution,
                "current_cost": round(current_cost, 2),
                "previous_cost": round(previous_cost, 2),
            }

        except Exception as e:
            logger.error(f"❌ Billing analysis failed: {e}")
            return {
                "has_anomalies": False,
                "anomalies": [],
                "summary": "分析服務暫時無法使用",
                "recommendations": [],
                "trend": "未知",
                "trend_percent": 0,
                "cost_attribution": {},
            }

    def _analyze_cost_attribution(self, billing_data: Dict[str, Any]) -> Dict[str, Any]:
        """成本歸因分析：識別主要費用來源"""
        top_services = billing_data.get("top_services", [])
        total_cost = billing_data.get("total_cost", 0)

        if total_cost == 0:
            return {"main_drivers": [], "top_percentage": 0}

        main_drivers = []
        cumulative_percentage = 0

        for service in top_services[:3]:  # Top 3 服務
            cost = service.get("cost", 0)
            percentage = (cost / total_cost) * 100
            cumulative_percentage += percentage

            main_drivers.append(
                {
                    "service": service.get("service", "Unknown"),
                    "cost": round(cost, 2),
                    "percentage": round(percentage, 2),
                }
            )

        return {
            "main_drivers": main_drivers,
            "top_percentage": round(cumulative_percentage, 2),
        }

    def _generate_basic_recommendations(
        self, billing_data: Dict[str, Any], anomalies: List[Dict], trend: str
    ) -> List[str]:
        """生成基礎優化建議（不使用 AI）"""
        recommendations = []

        # 檢查異常服務
        if anomalies:
            for anomaly in anomalies[:3]:
                service = anomaly.get("service", "Unknown")
                increase = anomaly.get("increase_percent", 0)
                recommendations.append(
                    f"⚠️ {service} 費用異常增長 {increase:.1f}%，建議立即檢查使用量和配置"
                )

        # 檢查 Top 服務
        top_services = billing_data.get("top_services", [])
        if top_services:
            top_service = top_services[0]
            service_name = top_service.get("service", "Unknown")
            cost = top_service.get("cost", 0)

            if "Cloud Run" in service_name:
                recommendations.append(
                    f"💡 Cloud Run 是最大費用來源 (${cost:.2f})，建議檢查 min-instances 設定和記憶體配置"
                )
            elif "Cloud Storage" in service_name:
                recommendations.append(
                    f"💡 Cloud Storage 費用較高 (${cost:.2f})，建議檢查 Lifecycle Policy 和冷儲存選項"
                )
            elif "Artifact Registry" in service_name:
                recommendations.append(
                    f"💡 Artifact Registry 費用較高 (${cost:.2f})，建議清理舊的 container images"
                )

        # 趨勢建議
        if trend == "上升":
            recommendations.append("📈 整體費用呈上升趨勢，建議定期審查資源使用情況")
        elif trend == "下降":
            recommendations.append("📉 整體費用呈下降趨勢，成本優化措施有效")

        # 如果沒有建議，添加默認建議
        if not recommendations:
            recommendations.append("✅ 系統運作正常，費用在合理範圍內")

        return recommendations

    def _generate_basic_summary(
        self,
        current_cost: float,
        previous_cost: float,
        trend: str,
        trend_percent: float,
        has_anomalies: bool,
    ) -> str:
        """生成基礎摘要（不使用 AI）"""
        summary = f"過去 7 天總費用為 ${current_cost:.2f}，"

        if previous_cost > 0:
            if trend == "上升":
                summary += f"較前期增加 ${abs(current_cost - previous_cost):.2f} ({abs(trend_percent):.1f}%)。"
            elif trend == "下降":
                summary += f"較前期減少 ${abs(current_cost - previous_cost):.2f} ({abs(trend_percent):.1f}%)。"
            else:
                summary += "與前期基本持平。"
        else:
            summary += "這是首次統計。"

        if has_anomalies:
            summary += " ⚠️ 偵測到異常費用增長，請檢查詳細報告。"
        else:
            summary += " 所有服務費用正常，無異常增長。"

        return summary

    async def _generate_ai_summary(
        self,
        current_data: Dict[str, Any],
        previous_data: Dict[str, Any],
        anomalies: List[Dict],
        trend: str,
        trend_percent: float,
    ) -> str:
        """使用 OpenAI GPT 生成分析摘要"""
        try:
            # 構建 prompt
            prompt = f"""你是一位 GCP 費用分析專家。請根據以下數據生成一份簡潔的分析摘要（2-3 句話）：

當前期間（過去 7 天）：
- 總費用：${current_data.get('total_cost', 0):.2f}
- Top 服務：{', '.join([s.get('service', 'Unknown') for s in current_data.get('top_services', [])[:3]])}

趨勢：{trend}（{trend_percent:+.1f}%）

異常情況：
{self._format_anomalies(anomalies) if anomalies else "無異常"}

請用繁體中文，語氣專業但友善，重點說明：
1. 費用總體情況
2. 主要費用來源
3. 是否有需要關注的異常

回應格式：只返回摘要文字，不要包含其他內容。
"""

            # 調用 OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位專業的 GCP 費用分析專家，擅長用簡潔易懂的語言解釋複雜的帳單數據。",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.7,
            )

            summary = response.choices[0].message.content.strip()
            logger.info("✅ AI summary generated successfully")
            return summary

        except Exception as e:
            logger.error(f"❌ AI summary generation failed: {e}")
            # Fallback to basic summary
            return self._generate_basic_summary(
                current_data.get("total_cost", 0),
                previous_data.get("total_cost", 0) - current_data.get("total_cost", 0),
                trend,
                trend_percent,
                len(anomalies) > 0,
            )

    def _format_anomalies(self, anomalies: List[Dict]) -> str:
        """格式化異常列表供 AI 分析"""
        if not anomalies:
            return "無異常"

        lines = []
        for anomaly in anomalies[:3]:
            service = anomaly.get("service", "Unknown")
            increase = anomaly.get("increase_percent", 0)
            current = anomaly.get("current_cost", 0)
            previous = anomaly.get("previous_cost", 0)
            lines.append(
                f"- {service}: ${previous:.2f} → ${current:.2f} (+{increase:.1f}%)"
            )

        return "\n".join(lines)


# 單例模式
_billing_analysis_service = None


def get_billing_analysis_service() -> BillingAnalysisService:
    """取得 BillingAnalysisService 單例"""
    global _billing_analysis_service
    if _billing_analysis_service is None:
        _billing_analysis_service = BillingAnalysisService()
    return _billing_analysis_service
