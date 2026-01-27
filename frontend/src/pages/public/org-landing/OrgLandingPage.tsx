import { useState, useRef } from 'react';
import { ChevronDown, CheckCircle, Zap, BarChart3, Users, MessageCircle, Mail, Phone, Download } from 'lucide-react';
import { Toast } from '@/components/ui/toast';

const OrgLandingPage = () => {
  const [showPricingCalculator, setShowPricingCalculator] = useState(false);
  const [showLeadForm, setShowLeadForm] = useState(false);
  const [showLineQR, setShowLineQR] = useState(false);
  
  // 報價計算機狀態
  const [students, setStudents] = useState(50);
  const [weeklyPractices, setWeeklyPractices] = useState(3);
  const [sentencesPerSession, setSentencesPerSession] = useState(15);
  const [teachers, setTeachers] = useState(10);
  const [contractType, setContractType] = useState<'1year' | '2years'>('1year');

  // 表單狀態
  const [formData, setFormData] = useState({
    schoolName: '',
    contactName: '',
    email: '',
    phone: '',
    city: '',
    teacherCount: '',
  });
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // 報價計算邏輯
  const calculateQuote = () => {
    const annualPoints = students * weeklyPractices * sentencesPerSession * 52;
    const pointPricePerUnit = 0.0015; // TWD
    const teacherPricePer1Year = 10.0; // USD (一年約)
    const teacherPricePer2Years = 9.0; // USD (兩年約)

    const contractYears = contractType === '1year' ? 1 : 2;
    const totalPoints = annualPoints * contractYears;
    const pointsCost = totalPoints * pointPricePerUnit;

    const giftTeachers = contractType === '1year' ? 3 : 5; // 贈送教師數
    const purchasedTeachers = Math.max(0, teachers - giftTeachers);
    const teacherPrice = contractType === '1year' ? teacherPricePer1Year : teacherPricePer2Years;
    const teacherCostUSD = purchasedTeachers * teacherPrice * 12 * contractYears;

    // 假設 USD=31 TWD
    const exchangeRate = 31;
    const teacherCostTWD = teacherCostUSD * exchangeRate;
    const totalTWD = pointsCost + teacherCostTWD;

    // 計算節省
    const oneYearQuote = (students * weeklyPractices * sentencesPerSession * 52 * pointPricePerUnit) + 
                        (purchasedTeachers * teacherPricePer1Year * 12 * exchangeRate);
    const savings = (oneYearQuote * 2) - totalTWD;
    const savingsPercent = ((savings / (oneYearQuote * 2)) * 100).toFixed(2);

    return {
      annualPoints,
      totalPoints,
      pointsCost: pointsCost.toFixed(2),
      giftTeachers,
      purchasedTeachers,
      teacherCostUSD: teacherCostUSD.toFixed(2),
      teacherCostTWD: teacherCostTWD.toFixed(0),
      totalTWD: totalTWD.toFixed(0),
      savings: savings > 0 ? savings.toFixed(0) : '0',
      savingsPercent,
    };
  };

  const quote = calculateQuote();
  const pricingRef = useRef<HTMLDivElement>(null);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.schoolName || !formData.email || !formData.phone) {
      setToast({ message: '請填寫所有必填欄位', type: 'error' });
      return;
    }

    // TODO: 實際應該傳送到後端或 CRM
    console.log('表單資料:', formData);
    
    setToast({ message: '感謝您的垂詢！業務人員將在 24 小時內聯絡您。', type: 'success' });
    setShowLeadForm(false);
    setFormData({
      schoolName: '',
      contactName: '',
      email: '',
      phone: '',
      city: '',
      teacherCount: '',
    });
  };

  const scrollToPricing = () => {
    pricingRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Duotopia
          </div>
          <button
            onClick={() => setShowLineQR(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
          >
            <MessageCircle size={18} />
            LINE 客服
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                AI 助教，不再是奢侈品
              </span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
              每位補習班老師都應該擁有 AI 助手。自動批改、數據分析、班級管理——
              <span className="font-semibold">比自己研發便宜 100 倍，比買教材便宜 50 倍</span>
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <button
                onClick={scrollToPricing}
                className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition transform hover:scale-105"
              >
                查看報價 <ChevronDown className="inline ml-2" size={20} />
              </button>
              <button
                onClick={() => setShowLineQR(true)}
                className="px-8 py-3 border-2 border-blue-600 text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition"
              >
                聯絡業務
              </button>
            </div>
          </div>

          {/* 問題 vs 解決方案對比 */}
          <div className="grid md:grid-cols-2 gap-8 mt-16">
            <div className="bg-red-50 border-2 border-red-200 rounded-xl p-8">
              <h3 className="text-2xl font-bold text-red-700 mb-6">🚫 訪間現況</h3>
              <ul className="space-y-4">
                <li className="flex gap-3">
                  <span className="text-red-500 font-bold">✗</span>
                  <span>老師花 40-60% 時間批改作業，沒時間備課</span>
                </li>
                <li className="flex gap-3">
                  <span className="text-red-500 font-bold">✗</span>
                  <span>各分校評分標準不一致，家長投訴多</span>
                </li>
                <li className="flex gap-3">
                  <span className="text-red-500 font-bold">✗</span>
                  <span>購買教材要一本本授權，費用高達百萬</span>
                </li>
                <li className="flex gap-3">
                  <span className="text-red-500 font-bold">✗</span>
                  <span>老師離職 = 學生流失，無法接班</span>
                </li>
                <li className="flex gap-3">
                  <span className="text-red-500 font-bold">✗</span>
                  <span>總部看不到各校數據，無法做決策</span>
                </li>
                <li className="flex gap-3">
                  <span className="text-red-500 font-bold">✗</span>
                  <span>自研系統？要 200-500 萬投資 + 3-6 個月</span>
                </li>
              </ul>
            </div>

            <div className="bg-green-50 border-2 border-green-200 rounded-xl p-8">
              <h3 className="text-2xl font-bold text-green-700 mb-6">✅ Duotopia 方案</h3>
              <ul className="space-y-4">
                <li className="flex gap-3">
                  <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                  <span><strong>AI 自動批改</strong> — 老師省 40% 時間，專注教學</span>
                </li>
                <li className="flex gap-3">
                  <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                  <span><strong>統一評分標準</strong> — 全機構一致，提升品質</span>
                </li>
                <li className="flex gap-3">
                  <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                  <span><strong>按用量計費</strong> — 無需購買教材授權，費用更低</span>
                </li>
                <li className="flex gap-3">
                  <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                  <span><strong>教材永久保存</strong> — 老師換人，記錄還在</span>
                </li>
                <li className="flex gap-3">
                  <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                  <span><strong>全機構 Dashboard</strong> — 實時數據，馬上決策</span>
                </li>
                <li className="flex gap-3">
                  <CheckCircle className="text-green-600 flex-shrink-0" size={24} />
                  <span><strong>立即使用</strong> — 無需開發，簽約即用</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 核心優勢展示 */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">Duotopia 核心優勢</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            {/* 優勢 1: AI 自動批改 */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-8 border border-blue-200">
              <div className="bg-blue-600 text-white rounded-lg p-4 w-fit mb-6">
                <Zap size={32} />
              </div>
              <h3 className="text-2xl font-bold mb-4 text-blue-900">⚡ AI 自動批改</h3>
              <p className="text-gray-700 mb-4">
                Azure 語音辨識 + AI 評分系統自動判分，省去 40-60% 批改時間
              </p>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>✓ 實時回饋給學生（鼓勵完成）</li>
                <li>✓ 標準化評分（家長滿意）</li>
                <li>✓ 無需人工審核</li>
              </ul>
              <p className="text-lg font-bold text-blue-600 mt-6">節省時間：24 小時 → 5 分鐘</p>
            </div>

            {/* 優勢 2: 全機構管理 */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-8 border border-purple-200">
              <div className="bg-purple-600 text-white rounded-lg p-4 w-fit mb-6">
                <Users size={32} />
              </div>
              <h3 className="text-2xl font-bold mb-4 text-purple-900">👥 全機構管理</h3>
              <p className="text-gray-700 mb-4">
                多分校、多師資、多班級統一管理，權限分級清晰
              </p>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>✓ 機構老闆看全景數據</li>
                <li>✓ 分校主任只看自己分校</li>
                <li>✓ 老師只看自己班級</li>
              </ul>
              <p className="text-lg font-bold text-purple-600 mt-6">支援規模：1-100+ 分校</p>
            </div>

            {/* 優勢 3: 數據驅動決策 */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-8 border border-green-200">
              <div className="bg-green-600 text-white rounded-lg p-4 w-fit mb-6">
                <BarChart3 size={32} />
              </div>
              <h3 className="text-2xl font-bold mb-4 text-green-900">📊 數據驅動決策</h3>
              <p className="text-gray-700 mb-4">
                實時 Dashboard，看得出哪個分校、哪位老師、哪些學生需要幫助
              </p>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>✓ 班級進度追蹤</li>
                <li>✓ 師資效能分析</li>
                <li>✓ 學生弱點診斷</li>
              </ul>
              <p className="text-lg font-bold text-green-600 mt-6">決策速度提升：50%</p>
            </div>
          </div>
        </div>
      </section>

      {/* ROI 計算 */}
      <section className="py-20 px-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">投資回報率 (ROI)</h2>
          
          <div className="grid md:grid-cols-4 gap-6 mb-12">
            <div className="bg-white/20 backdrop-blur rounded-xl p-6 text-center">
              <p className="text-5xl font-bold mb-2">40%</p>
              <p className="text-lg">老師時間節省</p>
            </div>
            <div className="bg-white/20 backdrop-blur rounded-xl p-6 text-center">
              <p className="text-5xl font-bold mb-2">24 萬</p>
              <p className="text-lg">年薪節省/老師</p>
            </div>
            <div className="bg-white/20 backdrop-blur rounded-xl p-6 text-center">
              <p className="text-5xl font-bold mb-2">10 位老師</p>
              <p className="text-lg">= 240 萬/年節省</p>
            </div>
            <div className="bg-white/20 backdrop-blur rounded-xl p-6 text-center">
              <p className="text-5xl font-bold mb-2">4 個月</p>
              <p className="text-lg">即可回本</p>
            </div>
          </div>

          <div className="bg-white/20 backdrop-blur rounded-xl p-8">
            <h3 className="text-2xl font-bold mb-6">💰 成本對比</h3>
            <div className="grid md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-blue-100 mb-2">自研系統</p>
                <p className="text-3xl font-bold">200-500 萬</p>
                <p className="text-sm text-blue-100 mt-2">+ 3-6 個月開發</p>
              </div>
              <div>
                <p className="text-sm text-blue-100 mb-2">買教材授權</p>
                <p className="text-3xl font-bold">100-300 萬</p>
                <p className="text-sm text-blue-100 mt-2">+ 持續費用</p>
              </div>
              <div className="border-2 border-white rounded-lg p-6">
                <p className="text-sm text-blue-100 mb-2">Duotopia</p>
                <p className="text-3xl font-bold">按使用量計費</p>
                <p className="text-sm text-blue-100 mt-2">立即使用，無隱藏費用</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 報價計算機 */}
      <section ref={pricingRef} className="py-20 px-4 bg-white">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-4">報價計算機</h2>
          <p className="text-center text-gray-600 mb-12 text-lg">輸入機構數據，立即看到報價</p>

          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-8 border border-blue-200">
            {/* 輸入區域 */}
            <div className="grid md:grid-cols-2 gap-8 mb-8">
              {/* 左側：基礎信息 */}
              <div className="space-y-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">基礎信息</h3>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    機構學生總數
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="10"
                      max="500"
                      value={students}
                      onChange={(e) => setStudents(Number(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-2xl font-bold text-blue-600 w-16">{students}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">建議：50-500 位學生</p>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    每位學生每週練習次數
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="1"
                      max="7"
                      value={weeklyPractices}
                      onChange={(e) => setWeeklyPractices(Number(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-2xl font-bold text-purple-600 w-16">{weeklyPractices} 次</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">預設：3 次/週</p>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    每次練習句數
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="5"
                      max="30"
                      value={sentencesPerSession}
                      onChange={(e) => setSentencesPerSession(Number(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-2xl font-bold text-pink-600 w-16">{sentencesPerSession} 句</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">預設：15 句/次</p>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    機構英文老師數
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="1"
                      max="100"
                      value={teachers}
                      onChange={(e) => setTeachers(Number(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-2xl font-bold text-green-600 w-16">{teachers} 位</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">建議：3-50 位老師</p>
                </div>
              </div>

              {/* 右側：合約類型 & 報價摘要 */}
              <div>
                <h3 className="text-xl font-bold text-gray-800 mb-4">合約方案</h3>
                
                <div className="space-y-3 mb-8">
                  <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer transition" 
                    style={{borderColor: contractType === '1year' ? '#3b82f6' : '#e5e7eb', 
                             backgroundColor: contractType === '1year' ? '#eff6ff' : '#f9fafb'}}>
                    <input
                      type="radio"
                      value="1year"
                      checked={contractType === '1year'}
                      onChange={(e) => setContractType(e.target.value as '1year' | '2years')}
                      className="w-4 h-4"
                    />
                    <span className="ml-3">
                      <strong className="text-lg">一年約</strong>
                      <p className="text-sm text-gray-600">高彈性，適合試用</p>
                    </span>
                  </label>

                  <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer transition" 
                    style={{borderColor: contractType === '2years' ? '#a855f7' : '#e5e7eb',
                             backgroundColor: contractType === '2years' ? '#faf5ff' : '#f9fafb'}}>
                    <input
                      type="radio"
                      value="2years"
                      checked={contractType === '2years'}
                      onChange={(e) => setContractType(e.target.value as '1year' | '2years')}
                      className="w-4 h-4"
                    />
                    <span className="ml-3">
                      <strong className="text-lg">兩年約 🎁</strong>
                      <p className="text-sm text-gray-600">享受優惠折扣 + 額外贈送老師授權</p>
                    </span>
                  </label>
                </div>

                {/* 報價摘要 */}
                <div className="bg-white rounded-xl p-6 border-2 border-blue-300">
                  <p className="text-sm text-gray-600 mb-4">預估 {contractType === '1year' ? '一年' : '兩年'}合約費用</p>
                  
                  <div className="space-y-3 mb-6">
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-gray-700">年度點數</span>
                      <span className="font-bold text-blue-600">{Number(quote.annualPoints).toLocaleString()} 點</span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-gray-700">點數費用</span>
                      <span className="font-bold">NT$ {Number(quote.pointsCost).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-gray-700">購買教師授權</span>
                      <span className="font-bold">{quote.purchasedTeachers} 位</span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-gray-700">教師授權費用</span>
                      <span className="font-bold">USD ${Number(quote.teacherCostUSD).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b">
                      <span className="text-gray-700">贈送教師授權</span>
                      <span className="font-bold text-green-600">+{quote.giftTeachers} 位 🎁</span>
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-blue-100 to-purple-100 rounded-lg p-4 mb-4">
                    <p className="text-sm text-gray-600 mb-1">合約總價 ({contractType === '1year' ? '一年' : '兩年'})</p>
                    <p className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                      NT$ {Number(quote.totalTWD).toLocaleString()}
                    </p>
                  </div>

                  {contractType === '2years' && Number(quote.savings) > 0 && (
                    <div className="bg-green-100 border border-green-300 rounded-lg p-3">
                      <p className="text-sm font-semibold text-green-800">
                        ✨ 兩年約節省 NT$ {Number(quote.savings).toLocaleString()} ({quote.savingsPercent}%)
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 行動按鈕 */}
            <div className="flex gap-4 pt-8 border-t">
              <button
                onClick={() => setShowLeadForm(true)}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition flex items-center justify-center gap-2"
              >
                <Download size={20} />
                下載報價單
              </button>
              <button
                onClick={() => setShowLineQR(true)}
                className="flex-1 px-6 py-3 border-2 border-green-500 text-green-600 rounded-lg font-semibold hover:bg-green-50 transition flex items-center justify-center gap-2"
              >
                <MessageCircle size={20} />
                詢問細節
              </button>
            </div>
          </div>

          {/* 說明文字 */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h4 className="font-bold text-blue-900 mb-3">📋 報價說明</h4>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>✓ 點數費用：以年度使用量計算，點數無使用期限</li>
              <li>✓ 教師授權：按授權人數計費，支持多分校共用額度</li>
              <li>✓ 贈送教師：兩年約贈送 5 位，一年約贈送 3 位</li>
              <li>✓ 此報價為預估，實際報價由業務確認後提供</li>
            </ul>
          </div>
        </div>
      </section>

      {/* 使用案例 */}
      <section className="py-20 px-4 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">適用對象</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            {/* 案例 1 */}
            <div className="bg-white rounded-xl p-8 shadow-md hover:shadow-lg transition">
              <div className="text-4xl mb-4">🏫</div>
              <h3 className="text-2xl font-bold mb-4">中小型補習班</h3>
              <p className="text-gray-600 mb-4">
                3-10 位老師、1-3 個校區，想要數位轉型
              </p>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>✓ 快速導入，無需大投資</li>
                <li>✓ 老師馬上可用</li>
                <li>✓ 按用量計費，風險低</li>
              </ul>
            </div>

            {/* 案例 2 */}
            <div className="bg-white rounded-xl p-8 shadow-md hover:shadow-lg transition">
              <div className="text-4xl mb-4">🏢</div>
              <h3 className="text-2xl font-bold mb-4">連鎖補習班集團</h3>
              <p className="text-gray-600 mb-4">
                50+ 位老師、5+ 個校區，需要統一管理
              </p>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>✓ 全機構 Dashboard</li>
                <li>✓ 權限分級管理</li>
                <li>✓ 數據驅動決策</li>
              </ul>
            </div>

            {/* 案例 3 */}
            <div className="bg-white rounded-xl p-8 shadow-md hover:shadow-lg transition">
              <div className="text-4xl mb-4">🎓</div>
              <h3 className="text-2xl font-bold mb-4">私立學校</h3>
              <p className="text-gray-600 mb-4">
                英文教師想要提升教學效率和學生滿意度
              </p>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>✓ 符合教育現場需求</li>
                <li>✓ 提升家長評價</li>
                <li>✓ 標準化評分系統</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-6">準備好了嗎？</h2>
          <p className="text-xl mb-8 opacity-90">
            填寫表單或掃描 QR Code，我們的業務團隊會在 24 小時內聯絡您，
            為您的機構量身定製方案
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <button
              onClick={() => setShowLeadForm(true)}
              className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:shadow-lg transition"
            >
              填寫表單 <Mail className="inline ml-2" size={20} />
            </button>
            <button
              onClick={() => setShowLineQR(true)}
              className="px-8 py-3 border-2 border-white text-white rounded-lg font-semibold hover:bg-white/10 transition"
            >
              掃描 QR Code <MessageCircle className="inline ml-2" size={20} />
            </button>
          </div>
        </div>
      </section>

      {/* 留下資料表單 Modal */}
      {showLeadForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 flex justify-between items-center">
              <h3 className="text-2xl font-bold">聯絡我們</h3>
              <button
                onClick={() => setShowLeadForm(false)}
                className="text-2xl hover:opacity-70 transition"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleFormSubmit} className="p-8 space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    機構名稱 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.schoolName}
                    onChange={(e) => setFormData({ ...formData, schoolName: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="例：ABC 補習班"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    聯絡人姓名 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.contactName}
                    onChange={(e) => setFormData({ ...formData, contactName: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="例：王小明"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    電子郵件 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="email@example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    手機號碼 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    required
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0912345678"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    所在城市
                  </label>
                  <select
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">選擇城市...</option>
                    <option value="taipei">台北市</option>
                    <option value="taichung">台中市</option>
                    <option value="kaohsiung">高雄市</option>
                    <option value="other">其他</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    機構英文老師數
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.teacherCount}
                    onChange={(e) => setFormData({ ...formData, teacherCount: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="10"
                  />
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-gray-700">
                  ✓ 我們會在 24 小時內聯絡您<br/>
                  ✓ 絕不會洩露您的個人資訊<br/>
                  ✓ 免費提供機構診斷與報價
                </p>
              </div>

              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => setShowLeadForm(false)}
                  className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition"
                >
                  送出表單並下載報價單
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* LINE QR Code Modal */}
      {showLineQR && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-8 text-center">
            <button
              onClick={() => setShowLineQR(false)}
              className="absolute top-4 right-4 text-2xl hover:opacity-70 transition"
            >
              ✕
            </button>

            <h3 className="text-2xl font-bold mb-4">LINE 官方客服</h3>
            <p className="text-gray-600 mb-6">掃描下方 QR Code 加好友，即時回答您的問題</p>

            {/* 假設 QR Code 圖片 */}
            <div className="bg-gray-100 rounded-lg p-6 mb-6 flex items-center justify-center h-64">
              <div className="text-center">
                <MessageCircle size={80} className="text-green-500 mx-auto mb-4 opacity-30" />
                <p className="text-gray-500 font-semibold">QR Code 圖片</p>
                <p className="text-sm text-gray-400">(實際實作時置換真實 QR Code)</p>
              </div>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <p className="text-sm text-gray-700">
                <strong>LINE ID:</strong> @duotopia_org<br/>
                <strong>營業時間:</strong> 週一~週五 09:00-18:00<br/>
                <strong>平均回覆時間:</strong> 5 分鐘內
              </p>
            </div>

            <button
              onClick={() => setShowLineQR(false)}
              className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition"
            >
              完成
            </button>
          </div>
        </div>
      )}

      {/* Toast 通知 */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="text-white font-bold mb-4">Duotopia</h4>
              <p className="text-sm">AI 助教平台，為補習班而生</p>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">產品</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">功能介紹</a></li>
                <li><a href="#" className="hover:text-white">報價方案</a></li>
                <li><a href="#" className="hover:text-white">使用案例</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">公司</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">關於我們</a></li>
                <li><a href="#" className="hover:text-white">聯絡方式</a></li>
                <li><a href="#" className="hover:text-white">隱私政策</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">聯絡我們</h4>
              <p className="text-sm">📧 org@duotopia.tw</p>
              <p className="text-sm">📱 0912-345-678</p>
              <p className="text-sm mt-4">LINE: @duotopia_org</p>
            </div>
          </div>
          <div className="border-t border-gray-700 pt-8 text-center text-sm">
            <p>&copy; 2024 Duotopia. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default OrgLandingPage;
