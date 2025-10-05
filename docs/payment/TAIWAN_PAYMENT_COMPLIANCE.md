# 台灣金流法規合規檢查清單

## 🇹🇼 台灣特定法規要求

### 1. **電子發票相關欄位（必須）**

```sql
-- 需要新增到 teacher_subscription_transactions 的欄位
ALTER TABLE teacher_subscription_transactions ADD COLUMN
    -- 發票基本資訊
    invoice_type VARCHAR(3) DEFAULT 'B2C',  -- B2B/B2C
    invoice_number VARCHAR(10),              -- 發票號碼 (如: AB12345678)
    invoice_date DATE,                       -- 開立日期
    invoice_status VARCHAR(20) DEFAULT 'PENDING',  -- ISSUED/CANCELLED/ALLOWANCE

    -- 買受人資訊
    buyer_tax_id VARCHAR(8),                 -- 統一編號 (8位數)
    buyer_name VARCHAR(100),                 -- 買受人名稱
    buyer_address VARCHAR(255),              -- 買受人地址
    buyer_email VARCHAR(255),                -- 買受人 email (電子發票用)

    -- 載具資訊
    carrier_type VARCHAR(10),                -- 載具類型 (3J0002=手機條碼)
    carrier_id VARCHAR(64),                  -- 載具號碼
    donate_mark CHAR(1) DEFAULT '0',         -- 是否捐贈 (0/1)
    love_code VARCHAR(10),                   -- 愛心碼

    -- 發票明細
    invoice_items JSON,                      -- 商品明細 JSON
    tax_type VARCHAR(10) DEFAULT 'TAXED',    -- 課稅別 (TAXED/ZERO/FREE)
    tax_rate DECIMAL(5,2) DEFAULT 5.00,      -- 稅率 (5%)
    tax_amount DECIMAL(10,2),                -- 稅額
    total_amount DECIMAL(10,2),              -- 總金額（含稅）

    -- 電子發票平台
    einvoice_upload_status VARCHAR(20),      -- 上傳狀態
    einvoice_upload_time TIMESTAMP,          -- 上傳時間
    einvoice_response JSON;                  -- 財政部回應
```

### 2. **統一編號驗證規則**

```python
def validate_taiwan_tax_id(tax_id: str) -> bool:
    """
    驗證台灣統一編號
    統編為8位數字，有特定的檢核邏輯
    """
    if not tax_id or len(tax_id) != 8:
        return False

    if not tax_id.isdigit():
        return False

    # 統一編號檢核邏輯
    weights = [1, 2, 1, 2, 1, 2, 4, 1]
    check_nums = []

    for i, digit in enumerate(tax_id):
        product = int(digit) * weights[i]
        # 兩位數要分開加總
        check_nums.append(product // 10 + product % 10)

    total = sum(check_nums)

    # 可被10整除 或 第7位是7且總和+1可被10整除
    return total % 10 == 0 or (tax_id[6] == '7' and (total + 1) % 10 == 0)
```

### 3. **發票開立時機與流程**

```python
# TapPay 金流與發票流程
class PaymentWithInvoiceFlow:
    """
    台灣法規要求：收到款項後48小時內開立發票
    """

    def process_payment(self, payment_data):
        # 1. TapPay 處理付款
        tappay_result = self.process_tappay(payment_data)

        # 2. 付款成功後立即開立發票
        if tappay_result.success:
            invoice_data = {
                'buyer_tax_id': payment_data.get('tax_id'),
                'buyer_name': payment_data.get('company_name'),
                'carrier_type': payment_data.get('carrier_type', '3J0002'),
                'carrier_id': payment_data.get('carrier_id'),  # 手機條碼
                'amount': payment_data['amount'],
                'tax_amount': payment_data['amount'] * 0.05 / 1.05,  # 內含稅額
            }

            # 3. 呼叫電子發票 API（綠界/藍新等）
            invoice_result = self.issue_einvoice(invoice_data)

            # 4. 上傳到財政部（2025年起必須即時）
            self.upload_to_einvoice_platform(invoice_result)

        return tappay_result, invoice_result
```

### 4. **發票服務商選擇**

| 服務商 | 特點 | 適合場景 |
|--------|------|----------|
| **綠界 ECPay** | 金流+發票整合 | 中小型電商 |
| **藍新 NewebPay** | 金流+發票整合 | 一般商家 |
| **ezPay 簡單付** | 發票專門 | 純發票需求 |
| **統一發票API** | 直連財政部 | 大型企業 |

### 5. **營業稅申報門檻（2025年）**

```
月營收門檻：
├─ < 8萬：免稅免發票
├─ 8-20萬：小規模營業人（1%營業稅）
└─ > 20萬：一般營業人（5%營業稅+開發票）

Duotopia 預估：
- 1000用戶 × NT$300 = NT$300,000/月
- 需要：開立發票 + 5%營業稅申報
```

## 🔧 實作建議

### Phase 1: MVP（現在）
1. **不處理統編** - 初期只做 B2C
2. **手動開發票** - 透過第三方平台
3. **使用現有欄位** - 統編存在 metadata

### Phase 2: 合規版（營收超過20萬時）
1. **整合發票API** - 綠界或藍新
2. **新增發票欄位** - 上述 SQL
3. **自動開立發票** - 付款成功後48小時內

### Phase 3: 企業版（B2B需求）
1. **統編驗證** - 即時驗證
2. **三聯式發票** - B2B專用
3. **月結功能** - 企業客戶需求

## ⚠️ 法律風險提醒

1. **未開發票罰則**
   - 漏開發票：罰款 3-30倍稅額
   - 2025年起未即時上傳：NT$1,500-15,000/次

2. **個資法要求**
   - 統編屬個資，需妥善保護
   - 需取得用戶同意才能儲存

3. **洗錢防制**
   - 單筆超過 50萬需通報
   - 需建立 KYC 機制

## 📊 架構師建議

### ✅ 現階段可行性評估
- **技術面**：現有設計足夠支撐 MVP
- **法規面**：初期可延後發票整合
- **成本面**：單表架構維護成本低

### ⚠️ 需立即處理
1. 在 metadata 中預留統編欄位
2. 記錄用戶是否需要統編發票
3. 準備發票開立的 SOP

### 📅 時程建議
- **0-3個月**：專注核心功能，手動開發票
- **3-6個月**：整合發票 API
- **6-12個月**：完整 B2B 功能

## 結論

現有的 `teacher_subscription_transactions` 設計：
- ✅ **適合初期** - 簡單有效
- ✅ **安全合規** - 符合 PCI DSS
- ⚠️ **需要擴充** - 發票相關欄位
- 💡 **建議做法** - 先用 metadata 存統編，之後再正式加欄位

**最重要的是：先上線賺錢，再逐步合規！**
