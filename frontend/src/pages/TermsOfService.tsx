import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Card className="p-8">
          <h1 className="text-3xl font-bold mb-4 text-center">使用者條款</h1>
          <p className="text-sm text-gray-600 mb-8 text-center">
            最後更新日期：2025年1月13日
          </p>

          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-6 text-gray-700">
              <section>
                <h2 className="text-xl font-semibold mb-3">1. 服務定義與範圍</h2>
                <div className="space-y-2 text-sm">
                  <p>1.1 Duotopia（以下稱「本服務」）是一個語言學習平台，提供互動式語言學習內容與評估服務。</p>
                  <p>1.2 本服務支援多種語言學習，包括但不限於英語、中文等語言的學習與練習。</p>
                  <p>1.3 用戶可透過本平台進行語言學習、完成作業、接受評估等學習活動。</p>
                  <p>1.4 學習內容與評估結果僅供教育用途使用。</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold mb-3">2. 用戶註冊與帳號管理</h2>
                <div className="space-y-2 text-sm">
                  <p>2.1 用戶須提供有效的電子郵件地址進行註冊。</p>
                  <p>2.2 用戶應妥善保管帳號密碼，對於帳號下的所有活動負完全責任。</p>
                  <p>2.3 若發現帳號遭未經授權使用，應立即通知本服務。</p>
                  <p>2.4 本服務保留隨時終止或暫停違反條款用戶帳號的權利。</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold mb-3">3. 著作權聲明</h2>
                <div className="space-y-2 text-sm">
                  <p>3.1 本服務提供的學習內容，其著作權屬於本公司或授權提供者所有。</p>
                  <p>3.2 用戶創建的學習記錄與作業內容，其著作權歸用戶所有。</p>
                  <p>3.3 用戶授權本服務使用其創建的內容以提供服務與改善系統。</p>
                  <p>3.4 學習內容僅供個人學習使用，不得進行商業使用或未經授權的散布。</p>
                  <p>3.5 本服務將妥善保存用戶的學習記錄，並依據隱私政策進行管理。</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold mb-3">4. 服務使用限制</h2>
                <div className="space-y-2 text-sm">
                  <p>4.1 用戶不得使用本服務進行任何違法或不當行為。</p>
                  <p>4.2 不得嘗試破壞、干擾或未經授權存取本服務系統。</p>
                  <p>4.3 不得使用本服務上傳或分享以下內容：</p>
                  <ul className="list-disc pl-6 space-y-1">
                    <li>侵犯他人著作權、商標權或其他智慧財產權的內容</li>
                    <li>違反法律法規的內容</li>
                    <li>惡意軟體、病毒或其他有害程式碼</li>
                    <li>不適當或冒犯性內容</li>
                  </ul>
                  <p>4.4 每個訂閱方案都有相應的使用限制，超出限制需升級方案。</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold mb-3">5. 隱私保護</h2>
                <div className="space-y-2 text-sm">
                  <p>5.1 本服務重視用戶隱私，詳細隱私保護措施請參閱隱私權政策。</p>
                  <p>5.2 本服務採用業界標準加密技術保護用戶資料。</p>
                  <p>5.3 學習記錄與個人資料將依法妥善保管。</p>
                  <p>5.4 用戶資料僅用於提供服務，不會未經同意分享給第三方。</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold mb-3">6. 付費與訂閱</h2>
                <div className="space-y-2 text-sm">
                  <p>6.1 本服務提供免費與付費訂閱方案。</p>
                  <p>6.2 付費方案的費用、功能與限制以網站公告為準。</p>
                  <p>6.3 訂閱費用採預付制，不提供部分退款。</p>
                  <p>6.4 用戶可隨時取消訂閱，但已支付的費用不予退還。</p>
                  <p>6.5 用戶可選擇變更方案，變更將於下個計費週期生效。</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold mb-3">7. 免責聲明</h2>
                <div className="space-y-2 text-sm">
                  <p>7.1 本服務使用AI技術進行語音評估，評估結果僅供參考。</p>
                  <p>7.2 本服務提供的學習內容盡力確保品質，但不保證完全準確或適合所有學習者。</p>
                  <p>7.3 本服務不對學習成效承擔保證責任。</p>
                  <p>7.4 用戶因使用本服務而產生的任何損失，本服務不承擔責任。</p>
                  <p>7.5 本服務可能因系統維護、升級或不可抗力因素暫時中斷，將盡快恢復服務。</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold mb-3">8. 條款修改</h2>
                <div className="space-y-2 text-sm">
                  <p>8.1 本服務保留隨時修改使用者條款的權利。</p>
                  <p>8.2 條款修改後將在網站公告，繼續使用本服務視為同意修改後的條款。</p>
                  <p>8.3 若不同意修改後的條款，用戶可選擇停止使用本服務。</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold mb-3">9. 準據法與管轄法院</h2>
                <div className="space-y-2 text-sm">
                  <p>9.1 本條款之解釋與適用，以中華民國法律為準據法。</p>
                  <p>9.2 因本條款所生之爭議，雙方同意以台灣台北地方法院為第一審管轄法院。</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold mb-3">10. 聯絡方式</h2>
                <div className="space-y-2 text-sm">
                  <p>梯加有限公司</p>
                  <p>統編：96752598</p>
                  <p>若對本條款有任何疑問，請透過以下方式聯絡我們：</p>
                  <p>電子郵件：myduotopia@gmail.com</p>
                </div>
              </section>
            </div>
          </ScrollArea>
        </Card>
      </div>
    </div>
  );
}
