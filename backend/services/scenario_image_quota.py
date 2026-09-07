"""情境對話 AI 生圖的每月次數上限（issue #1024）。

生圖比文字生成貴一個量級，而且是**逐題觸發**的（一份 10 題就可能按 10 次），所以在
完整配額（#1025）做好之前，先擋一道。

規則刻意簡單：**每位老師每個自然月 FREE_MONTHLY_LIMIT 次，用完就擋，不接點數。**
與 ``magic_paste_quota`` 的差別就在這裡 —— 那邊用完會走 QuotaService waterfall
（訂閱 → 點數包）扣點。這裡不做，因為計價方式還沒定（#1025），先用「擋下來」換取
成本可控；等 #1025 決定好再把 :func:`consume` 換成 waterfall，計數表可以直接沿用。

並發處理沿用 magic_paste 的作法：SELECT ... FOR UPDATE 鎖住當月計數列，讓同一位老師
的 consume 序列化，避免 check-then-increment 的競態把額度多花。
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import ScenarioImageUsage, Teacher

# 每位老師每月免費生圖張數。
#
# 抓 30 是「夠用但不至於失控」：一份情境對話最多 10 題，等於一個月可以做三份全圖的
# 教材。實際額度等 #1025 有真實用量數據再調。
FREE_MONTHLY_LIMIT = 30


def current_year_month() -> str:
    """回傳目前的自然月字串 'YYYY-MM'（UTC）。"""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _get_usage(
    db: Session, teacher_id: int, year_month: str
) -> Optional[ScenarioImageUsage]:
    return (
        db.query(ScenarioImageUsage)
        .filter(
            ScenarioImageUsage.teacher_id == teacher_id,
            ScenarioImageUsage.year_month == year_month,
        )
        .first()
    )


def _get_or_create_usage_locked(
    db: Session, teacher_id: int, year_month: str
) -> ScenarioImageUsage:
    """取得（或建立）當月計數列並鎖住，讓同一位老師的 consume 序列化。

    首次建立靠 UNIQUE(teacher_id, year_month) 擋並發，衝突就改讀對方建立的那列。
    （SQLite 不支援 FOR UPDATE，SQLAlchemy 會自動忽略，測試不受影響。）
    """
    row = (
        db.query(ScenarioImageUsage)
        .filter(
            ScenarioImageUsage.teacher_id == teacher_id,
            ScenarioImageUsage.year_month == year_month,
        )
        .with_for_update()
        .first()
    )
    if row is not None:
        return row

    row = ScenarioImageUsage(teacher_id=teacher_id, year_month=year_month, count=0)
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        row = (
            db.query(ScenarioImageUsage)
            .filter(
                ScenarioImageUsage.teacher_id == teacher_id,
                ScenarioImageUsage.year_month == year_month,
            )
            .with_for_update()
            .first()
        )
    return row


def get_quota_status(
    db: Session, teacher: Teacher, year_month: Optional[str] = None
) -> Dict[str, Any]:
    """目前的配額狀態，供前端顯示剩餘次數。"""
    ym = year_month or current_year_month()
    row = _get_usage(db, teacher.id, ym)
    used = row.count if row else 0
    remaining = max(0, FREE_MONTHLY_LIMIT - used)
    return {
        "year_month": ym,
        "limit": FREE_MONTHLY_LIMIT,
        "used": used,
        "remaining": remaining,
        "can_use": remaining > 0,
    }


def consume(
    db: Session, teacher: Teacher, year_month: Optional[str] = None
) -> Dict[str, Any]:
    """**先保留**一次額度（在打 AI 之前呼叫）。

    額度用完會回 ``{"charged": None, ...}`` 而不是丟例外，讓呼叫端決定回什麼狀態碼。
    呼叫端**一定要看這個回傳值** —— 只在打 AI 之前查一次 :func:`get_quota_status` 是
    擋不住並發的：同一位老師在 29/30 時同時送兩個請求，兩個都會通過那次檢查
    （PR #1027 review）。所以正確用法是「先 consume 佔位 → 再打 AI → 失敗就
    :func:`refund`」，而不是「先查 → 打 AI → 再 consume」。
    """
    ym = year_month or current_year_month()
    row = _get_or_create_usage_locked(db, teacher.id, ym)

    if row.count >= FREE_MONTHLY_LIMIT:
        db.commit()
        return {
            "charged": None,
            "year_month": ym,
            "limit": FREE_MONTHLY_LIMIT,
            "used": row.count,
            "remaining": 0,
            "can_use": False,
        }

    row.count += 1
    db.commit()
    db.refresh(row)
    return {
        "charged": "free",
        "year_month": ym,
        "limit": FREE_MONTHLY_LIMIT,
        "used": row.count,
        "remaining": max(0, FREE_MONTHLY_LIMIT - row.count),
        "can_use": row.count < FREE_MONTHLY_LIMIT,
    }


def refund(
    db: Session, teacher: Teacher, year_month: Optional[str] = None
) -> Dict[str, Any]:
    """把先前保留的一次額度還回去。

    用在「保留成功但後續失敗」：被安全過濾擋下、圖存不進去。老師沒拿到圖，就不該
    被算一次（比照 magic_paste 擷取到 0 項不扣額的產品決策）。

    計數不會被扣到負數 —— 就算重複退款（例外處理路徑重入）也只是回到 0。
    """
    ym = year_month or current_year_month()
    row = _get_or_create_usage_locked(db, teacher.id, ym)
    row.count = max(0, row.count - 1)
    db.commit()
    db.refresh(row)
    return {
        "year_month": ym,
        "limit": FREE_MONTHLY_LIMIT,
        "used": row.count,
        "remaining": max(0, FREE_MONTHLY_LIMIT - row.count),
        "can_use": row.count < FREE_MONTHLY_LIMIT,
    }
