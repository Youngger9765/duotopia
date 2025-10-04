# TapPay 金流串接指南

## 概述
TapPay 是台灣的第三方金流服務商，提供信用卡、LINE Pay、Apple Pay 等多種支付方式。

## 串接架構

```
┌─────────┐     ┌─────────┐     ┌──────────┐
│ Frontend│────▶│ Backend │────▶│ TapPay   │
│ (React) │     │ (Python)│     │ API      │
└─────────┘     └─────────┘     └──────────┘
     │               ▲                │
     │               │                │
     └───────────────┴────────────────┘
         Prime Token / Response
```

## 一、環境設定

### 測試環境
- Sandbox URL: `https://sandbox.tappaysdk.com`
- 測試卡號: `4242 4242 4242 4242`
- 有效期限: 任何未來日期
- CVV: `123`

### 正式環境
- Production URL: `https://prod.tappaysdk.com`

## 二、Frontend 整合 (React + TypeScript)

### 1. 安裝 SDK

在 `index.html` 加入：
```html
<script src="https://js.tappaysdk.com/sdk/tpdirect/v5.17.0" 
        type="text/javascript" 
        crossorigin="anonymous">
</script>
```

### 2. TypeScript 型別定義

創建 `src/types/tappay.d.ts`:
```typescript
declare global {
  interface Window {
    TPDirect: {
      setupSDK: (appId: number, appKey: string, serverType: string) => void;
      card: {
        setup: (config: CardSetupConfig) => void;
        onUpdate: (callback: (update: UpdateResult) => void) => void;
        getPrime: (callback: (result: PrimeResult) => void) => void;
      };
    };
  }
}

interface CardSetupConfig {
  fields: {
    number: {
      element: string;
      placeholder: string;
    };
    expirationDate: {
      element: string;
      placeholder: string;
    };
    ccv: {
      element: string;
      placeholder: string;
    };
  };
  styles?: string;
  isMaskCreditCardNumber?: boolean;
  maskCreditCardNumberRange?: {
    beginIndex: number;
    endIndex: number;
  };
}

interface UpdateResult {
  canGetPrime: boolean;
  hasError: boolean;
  status: {
    number: number;
    expiry: number;
    ccv: number;
  };
}

interface PrimeResult {
  status: number;
  msg: string;
  prime?: string;
  card?: {
    lastfour: string;
    type: number;
    country: string;
    countryCode: string;
    funding: number;
  };
}

export {};
```

### 3. React 付款組件

創建 `src/components/TapPayPayment.tsx`:
```typescript
import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';

interface TapPayPaymentProps {
  amount: number;
  onPaymentSuccess: (transactionId: string) => void;
  onPaymentError: (error: string) => void;
}

const TapPayPayment: React.FC<TapPayPaymentProps> = ({
  amount,
  onPaymentSuccess,
  onPaymentError
}) => {
  const [canSubmit, setCanSubmit] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    // 初始化 TapPay SDK
    const APP_ID = import.meta.env.VITE_TAPPAY_APP_ID;
    const APP_KEY = import.meta.env.VITE_TAPPAY_APP_KEY;
    const SERVER_TYPE = import.meta.env.VITE_TAPPAY_SERVER_TYPE || 'sandbox';

    if (window.TPDirect) {
      window.TPDirect.setupSDK(
        parseInt(APP_ID),
        APP_KEY,
        SERVER_TYPE
      );

      // 設定信用卡表單
      window.TPDirect.card.setup({
        fields: {
          number: {
            element: '#card-number',
            placeholder: '**** **** **** ****'
          },
          expirationDate: {
            element: '#card-expiration-date',
            placeholder: 'MM / YY'
          },
          ccv: {
            element: '#card-ccv',
            placeholder: 'CVV'
          }
        },
        styles: `
          input {
            font-size: 16px;
            color: #333;
            border: 1px solid #ddd;
            padding: 12px;
            border-radius: 4px;
            width: 100%;
          }
          input:focus {
            border-color: #4F46E5;
            outline: none;
          }
          .has-error {
            border-color: #EF4444;
          }
        `,
        isMaskCreditCardNumber: true,
        maskCreditCardNumberRange: {
          beginIndex: 6,
          endIndex: 11
        }
      });

      // 監聽表單狀態
      window.TPDirect.card.onUpdate((update) => {
        setCanSubmit(update.canGetPrime);
        
        // 顯示錯誤訊息
        if (update.status.number === 2) {
          document.getElementById('card-number')?.classList.add('has-error');
        } else {
          document.getElementById('card-number')?.classList.remove('has-error');
        }
      });
    }
  }, []);

  const handleSubmit = async () => {
    if (!canSubmit) {
      toast.error('請檢查信用卡資訊');
      return;
    }

    setIsProcessing(true);

    // 取得 Prime Token
    window.TPDirect.card.getPrime(async (result) => {
      if (result.status !== 0) {
        onPaymentError(result.msg);
        setIsProcessing(false);
        return;
      }

      try {
        // 發送到後端處理付款
        const response = await fetch('/api/payment/process', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            prime: result.prime,
            amount: amount,
            details: {
              item_name: 'Duotopia 訂閱方案',
              item_price: amount
            }
          })
        });

        const data = await response.json();

        if (data.success) {
          onPaymentSuccess(data.transaction_id);
          toast.success('付款成功！');
        } else {
          onPaymentError(data.message);
          toast.error(data.message);
        }
      } catch (error) {
        onPaymentError('付款處理失敗');
        toast.error('付款處理失敗');
      } finally {
        setIsProcessing(false);
      }
    });
  };

  return (
    <Card className="w-full max-w-lg mx-auto">
      <CardHeader>
        <CardTitle>信用卡付款</CardTitle>
        <p className="text-sm text-gray-600">金額: NT$ {amount.toLocaleString()}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">卡號</label>
          <div id="card-number" className="tappay-field"></div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">有效期限</label>
            <div id="card-expiration-date" className="tappay-field"></div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">安全碼</label>
            <div id="card-ccv" className="tappay-field"></div>
          </div>
        </div>

        <Button 
          onClick={handleSubmit}
          disabled={!canSubmit || isProcessing}
          className="w-full"
        >
          {isProcessing ? '處理中...' : `支付 NT$ ${amount.toLocaleString()}`}
        </Button>

        <div className="text-xs text-gray-500 text-center">
          <p>測試卡號: 4242 4242 4242 4242</p>
          <p>有效期限: 任何未來日期 | CVV: 123</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default TapPayPayment;
```

## 三、Backend 整合 (Python FastAPI)

### 1. 安裝套件

```bash
pip install httpx pydantic
```

### 2. TapPay Service

創建 `backend/services/tappay_service.py`:
```python
import httpx
from typing import Dict, Any, Optional
from pydantic import BaseModel
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PaymentRequest(BaseModel):
    prime: str
    amount: int
    details: Dict[str, Any]
    cardholder_email: Optional[str] = None
    cardholder_name: Optional[str] = None
    cardholder_phone: Optional[str] = None

class TapPayService:
    def __init__(self):
        self.partner_key = os.getenv('TAPPAY_PARTNER_KEY')
        self.merchant_id = os.getenv('TAPPAY_MERCHANT_ID')
        self.is_sandbox = os.getenv('TAPPAY_SERVER_TYPE', 'sandbox') == 'sandbox'
        
        self.base_url = (
            'https://sandbox.tappaysdk.com' if self.is_sandbox 
            else 'https://prod.tappaysdk.com'
        )
        
    async def process_payment(self, payment_data: PaymentRequest) -> Dict[str, Any]:
        """處理付款"""
        
        endpoint = f"{self.base_url}/tpc/payment/pay-by-prime"
        
        payload = {
            "partner_key": self.partner_key,
            "merchant_id": self.merchant_id,
            "amount": payment_data.amount,
            "currency": "TWD",
            "details": payment_data.details.get('item_name', 'Duotopia Subscription'),
            "prime": payment_data.prime,
            "order_number": self._generate_order_number(),
            "bank_transaction_id": "",
            "cardholder": {
                "phone_number": payment_data.cardholder_phone or "+886987654321",
                "name": payment_data.cardholder_name or "User",
                "email": payment_data.cardholder_email or "user@example.com",
            },
            "remember": True,  # 記住卡片資訊供未來使用
            "result_url": {
                "frontend_redirect_url": f"{os.getenv('FRONTEND_URL')}/payment/result",
                "backend_notify_url": f"{os.getenv('BACKEND_URL')}/api/payment/notify"
            },
            "three_domain_secure": False  # 設為 True 啟用 3D 驗證
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                result = response.json()
                
                if result.get("status") == 0:
                    # 付款成功
                    return {
                        "success": True,
                        "transaction_id": result.get("rec_trade_id"),
                        "bank_transaction_id": result.get("bank_transaction_id"),
                        "card_info": result.get("card_info"),
                        "card_secret": result.get("card_secret")  # 包含 card_key 和 card_token
                    }
                else:
                    # 付款失敗
                    logger.error(f"Payment failed: {result}")
                    return {
                        "success": False,
                        "message": result.get("msg", "付款失敗"),
                        "status": result.get("status")
                    }
                    
        except httpx.TimeoutException:
            logger.error("Payment timeout")
            return {
                "success": False,
                "message": "付款處理超時，請稍後重試"
            }
        except Exception as e:
            logger.error(f"Payment error: {str(e)}")
            return {
                "success": False,
                "message": "付款處理發生錯誤"
            }
    
    async def refund_payment(
        self, 
        rec_trade_id: str, 
        amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """退款"""
        
        endpoint = f"{self.base_url}/tpc/transaction/refund"
        
        payload = {
            "partner_key": self.partner_key,
            "rec_trade_id": rec_trade_id
        }
        
        if amount:
            payload["amount"] = amount  # 部分退款
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                result = response.json()
                
                return {
                    "success": result.get("status") == 0,
                    "refund_id": result.get("refund_id"),
                    "message": result.get("msg")
                }
                
        except Exception as e:
            logger.error(f"Refund error: {str(e)}")
            return {
                "success": False,
                "message": "退款處理發生錯誤"
            }
    
    async def query_payment(self, rec_trade_id: str) -> Dict[str, Any]:
        """查詢付款狀態"""
        
        endpoint = f"{self.base_url}/tpc/transaction/query"
        
        payload = {
            "partner_key": self.partner_key,
            "filters": {
                "rec_trade_id": rec_trade_id
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                result = response.json()
                
                if result.get("status") == 0:
                    trades = result.get("trade_records", [])
                    if trades:
                        return {
                            "success": True,
                            "trade_record": trades[0]
                        }
                
                return {
                    "success": False,
                    "message": "找不到交易記錄"
                }
                
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            return {
                "success": False,
                "message": "查詢發生錯誤"
            }
    
    def _generate_order_number(self) -> str:
        """產生訂單編號"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"DUO{timestamp}"
```

### 3. API 路由

創建 `backend/routers/payment.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from ..services.tappay_service import TapPayService, PaymentRequest
from ..dependencies import get_current_user
from ..models import User, Payment
from ..database import get_db
from sqlalchemy.orm import Session
import logging

router = APIRouter(prefix="/api/payment", tags=["payment"])
logger = logging.getLogger(__name__)

@router.post("/process")
async def process_payment(
    payment_data: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """處理付款"""
    
    # 加入用戶資訊
    payment_data.cardholder_email = current_user.email
    payment_data.cardholder_name = current_user.name
    
    # 使用 TapPay Service 處理付款
    tappay_service = TapPayService()
    result = await tappay_service.process_payment(payment_data)
    
    if result["success"]:
        # 儲存付款記錄到資料庫
        payment = Payment(
            user_id=current_user.id,
            amount=payment_data.amount,
            currency="TWD",
            transaction_id=result["transaction_id"],
            status="SUCCESS",
            payment_method="CREDIT_CARD"
        )
        
        # 如果有記住卡片，儲存 token
        if result.get("card_secret"):
            payment.card_token = result["card_secret"]["card_token"]
            payment.card_key = result["card_secret"]["card_key"]
            
        db.add(payment)
        db.commit()
        
        # 更新用戶訂閱狀態
        current_user.subscription_status = "active"
        current_user.subscription_end_date = datetime.now() + timedelta(days=30)
        db.commit()
        
        return {
            "success": True,
            "transaction_id": result["transaction_id"],
            "message": "付款成功"
        }
    else:
        # 記錄失敗的付款
        payment = Payment(
            user_id=current_user.id,
            amount=payment_data.amount,
            currency="TWD",
            status="FAILED",
            error_message=result.get("message")
        )
        db.add(payment)
        db.commit()
        
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "付款失敗")
        )

@router.post("/notify")
async def payment_notify(
    notification: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """接收 TapPay Backend Notify"""
    
    logger.info(f"Received payment notification: {notification}")
    
    # 驗證並更新付款狀態
    rec_trade_id = notification.get("rec_trade_id")
    status = notification.get("status")
    
    if rec_trade_id:
        payment = db.query(Payment).filter_by(
            transaction_id=rec_trade_id
        ).first()
        
        if payment:
            if status == 0:
                payment.status = "SUCCESS"
            else:
                payment.status = "FAILED"
                payment.error_message = notification.get("msg")
            
            db.commit()
    
    # 必須返回 200 OK，否則 TapPay 會重試
    return {"status": "ok"}

@router.get("/status/{transaction_id}")
async def check_payment_status(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查詢付款狀態"""
    
    payment = db.query(Payment).filter_by(
        transaction_id=transaction_id,
        user_id=current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="找不到付款記錄")
    
    # 從 TapPay 查詢最新狀態
    tappay_service = TapPayService()
    result = await tappay_service.query_payment(transaction_id)
    
    if result["success"]:
        trade_record = result["trade_record"]
        return {
            "transaction_id": transaction_id,
            "amount": trade_record.get("amount"),
            "status": trade_record.get("record_status"),
            "bank_transaction_id": trade_record.get("bank_transaction_id"),
            "created_at": payment.created_at
        }
    else:
        return {
            "transaction_id": transaction_id,
            "status": payment.status,
            "message": result.get("message")
        }

@router.post("/refund/{transaction_id}")
async def refund_payment(
    transaction_id: str,
    amount: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """申請退款"""
    
    # 檢查權限（只有管理員可以退款）
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="無權限執行此操作")
    
    payment = db.query(Payment).filter_by(
        transaction_id=transaction_id
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="找不到付款記錄")
    
    if payment.status != "SUCCESS":
        raise HTTPException(status_code=400, detail="只能退款成功的交易")
    
    # 執行退款
    tappay_service = TapPayService()
    result = await tappay_service.refund_payment(transaction_id, amount)
    
    if result["success"]:
        # 更新付款記錄
        if amount and amount < payment.amount:
            payment.status = "PARTIALLY_REFUNDED"
            payment.refunded_amount = amount
        else:
            payment.status = "REFUNDED"
            payment.refunded_amount = payment.amount
        
        payment.refund_id = result["refund_id"]
        db.commit()
        
        return {
            "success": True,
            "refund_id": result["refund_id"],
            "message": "退款申請成功"
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "退款失敗")
        )
```

## 四、環境變數設定

### `.env` 檔案
```env
# TapPay 設定
VITE_TAPPAY_APP_ID=12345
VITE_TAPPAY_APP_KEY=app_key_from_tappay
VITE_TAPPAY_SERVER_TYPE=sandbox

# Backend TapPay
TAPPAY_PARTNER_KEY=partner_key_from_tappay
TAPPAY_MERCHANT_ID=merchant_id_from_tappay
TAPPAY_SERVER_TYPE=sandbox

# URLs
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
```

## 五、資料庫 Schema

```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'TWD',
    transaction_id VARCHAR(255) UNIQUE,
    bank_transaction_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50),
    card_token TEXT,
    card_key TEXT,
    refund_id VARCHAR(255),
    refunded_amount INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_transaction_id ON payments(transaction_id);
CREATE INDEX idx_payments_status ON payments(status);
```

## 六、安全注意事項

1. **絕對不要在前端儲存**：
   - Partner Key
   - Merchant ID
   - Card Token / Card Key

2. **HTTPS 必要性**：
   - 生產環境必須使用 HTTPS
   - Backend Notify URL 必須是 HTTPS

3. **PCI DSS 合規**：
   - 不要在自己的伺服器儲存完整卡號
   - 使用 TapPay 的 Token 機制

4. **錯誤處理**：
   - 不要向用戶顯示詳細的錯誤訊息
   - 記錄完整錯誤供內部除錯

## 七、測試流程

### 1. 單元測試
```python
# tests/test_payment.py
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_process_payment_success():
    """測試成功付款流程"""
    with patch('services.tappay_service.TapPayService.process_payment') as mock:
        mock.return_value = {
            "success": True,
            "transaction_id": "TEST_TRANS_001"
        }
        
        # 測試 API
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/payment/process",
                json={
                    "prime": "test_prime_token",
                    "amount": 1000,
                    "details": {"item_name": "Test Item"}
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
        assert response.status_code == 200
        assert response.json()["success"] is True
```

### 2. 整合測試
- 使用 TapPay Sandbox 環境
- 測試完整付款流程
- 測試 Webhook 接收
- 測試退款流程

## 八、常見問題

### Q1: Prime Token 過期
**A**: Prime Token 只有 90 秒有效期，必須在用戶提交表單時即時取得。

### Q2: Backend Notify 沒收到
**A**: 
- 確認 URL 可以從外部訪問
- 確認返回 HTTP 200
- 檢查防火牆設定

### Q3: 3D 驗證流程
**A**: 設定 `three_domain_secure: true`，用戶會被導向銀行驗證頁面。

### Q4: 定期扣款
**A**: 使用儲存的 card_token 和 card_key 呼叫 Pay by Card Token API。

## 九、上線檢查清單

- [ ] 更換為正式環境的 App ID、App Key、Partner Key
- [ ] 更新 API URL 為正式環境
- [ ] 確認 HTTPS 設定
- [ ] 設定 Backend Notify URL
- [ ] 測試真實信用卡交易
- [ ] 設定監控和告警
- [ ] 準備客服處理退款流程
- [ ] 確認 PCI DSS 合規性

## 參考資源

- [TapPay 官方文件](https://docs.tappaysdk.com)
- [TapPay Web Example](https://github.com/TapPay/tappay-web-example)
- [TapPay Node.js SDK](https://github.com/TapPay/tappay-nodejs)