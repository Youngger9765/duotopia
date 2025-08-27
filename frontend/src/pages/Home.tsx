import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { 
  GraduationCap, 
  Users, 
  Sparkles, 
  Brain, 
  Mic, 
  Trophy,
  BarChart3,
  Globe,
  Shield,
  Zap,
  CheckCircle,
  ArrowRight,
  Play,
  Star
} from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white overflow-hidden">
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse"></div>
        
        <div className="relative container mx-auto px-4 py-24 lg:py-32">
          <div className="max-w-6xl mx-auto">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <div className="flex items-center space-x-2 mb-6">
                  <Sparkles className="h-6 w-6 text-yellow-400" />
                  <span className="text-yellow-400 font-semibold">AI 驅動的英語學習革命</span>
                </div>
                <h1 className="text-5xl lg:text-6xl font-bold mb-6 leading-tight">
                  Duotopia
                  <span className="block text-3xl lg:text-4xl mt-2 text-blue-200">
                    多元智能英語學習平台
                  </span>
                </h1>
                <p className="text-xl mb-8 text-blue-100 leading-relaxed">
                  透過 AI 語音辨識與即時回饋，為 6-15 歲學生打造個人化的英語口說學習體驗。
                  讓每個孩子都能自信開口說英語！
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link to="/teacher/register">
                    <Button size="lg" className="bg-white text-blue-700 hover:bg-gray-100 px-8 py-6 text-lg font-semibold shadow-xl">
                      <GraduationCap className="mr-2 h-5 w-5" />
                      免費試用
                    </Button>
                  </Link>
                  <Button 
                    size="lg" 
                    variant="outline" 
                    className="border-white text-white hover:bg-white hover:text-blue-700 px-8 py-6 text-lg"
                  >
                    <Play className="mr-2 h-5 w-5" />
                    觀看介紹影片
                  </Button>
                </div>
                <div className="mt-8 flex items-center space-x-6">
                  <div className="flex -space-x-2">
                    {[1,2,3,4].map(i => (
                      <div key={i} className="w-10 h-10 bg-gradient-to-br from-blue-400 to-indigo-400 rounded-full border-2 border-white"></div>
                    ))}
                  </div>
                  <div className="text-sm">
                    <div className="font-semibold">超過 1,000+ 教師信賴</div>
                    <div className="text-blue-200">10,000+ 學生正在使用</div>
                  </div>
                </div>
              </div>
              <div className="hidden lg:block">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-indigo-400 rounded-3xl transform rotate-3"></div>
                  <img 
                    src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600" 
                    alt="Students learning" 
                    className="relative rounded-3xl shadow-2xl"
                  />
                  <div className="absolute -bottom-6 -left-6 bg-white rounded-xl shadow-xl p-4 flex items-center space-x-3">
                    <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    </div>
                    <div>
                      <div className="font-semibold">AI 即時回饋</div>
                      <div className="text-sm text-gray-600">精準發音評測</div>
                    </div>
                  </div>
                  <div className="absolute -top-6 -right-6 bg-white rounded-xl shadow-xl p-4 flex items-center space-x-3">
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <Brain className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                      <div className="font-semibold">個人化學習</div>
                      <div className="text-sm text-gray-600">適性化教材</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Badges */}
      <section className="bg-gray-50 py-12 border-b">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 items-center">
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">98%</div>
                <div className="text-sm text-gray-600 mt-1">學生滿意度</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">3個月</div>
                <div className="text-sm text-gray-600 mt-1">平均進步時間</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">50%</div>
                <div className="text-sm text-gray-600 mt-1">口說能力提升</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">24/7</div>
                <div className="text-sm text-gray-600 mt-1">隨時隨地學習</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 lg:py-28">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                為什麼選擇 Duotopia？
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                結合最新 AI 技術與教育心理學，打造最適合亞洲學生的英語口說訓練平台
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Mic className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">AI 語音辨識</h3>
                <p className="text-gray-600 mb-4">
                  採用先進的語音辨識技術，精準評估發音、語調、流暢度，提供即時回饋與改進建議
                </p>
                <Link to="/teacher/register" className="text-blue-600 font-semibold flex items-center hover:text-blue-700">
                  了解更多 <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>

              {/* Feature 2 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Brain className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">多元智能學習</h3>
                <p className="text-gray-600 mb-4">
                  六種活動類型涵蓋聽說讀寫，從朗讀到情境對話，全方位提升英語能力
                </p>
                <Link to="/teacher/register" className="text-blue-600 font-semibold flex items-center hover:text-blue-700">
                  了解更多 <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>

              {/* Feature 3 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <BarChart3 className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">學習數據分析</h3>
                <p className="text-gray-600 mb-4">
                  詳細的學習報告與進度追蹤，讓教師和家長清楚掌握孩子的學習狀況
                </p>
                <Link to="/teacher/register" className="text-blue-600 font-semibold flex items-center hover:text-blue-700">
                  了解更多 <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>

              {/* Feature 4 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-orange-500 to-red-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Trophy className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">遊戲化激勵</h3>
                <p className="text-gray-600 mb-4">
                  透過積分、徽章、排行榜等遊戲化元素，提高學習動機與參與度
                </p>
                <Link to="/teacher/register" className="text-blue-600 font-semibold flex items-center hover:text-blue-700">
                  了解更多 <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>

              {/* Feature 5 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Shield className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">安全可靠</h3>
                <p className="text-gray-600 mb-4">
                  符合 COPPA 與 GDPR 規範，保護學生隱私，讓家長安心
                </p>
                <Link to="/teacher/register" className="text-blue-600 font-semibold flex items-center hover:text-blue-700">
                  了解更多 <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>

              {/* Feature 6 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-teal-500 to-green-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Zap className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">簡單易用</h3>
                <p className="text-gray-600 mb-4">
                  直覺的介面設計，教師 5 分鐘即可上手，學生無需額外訓練
                </p>
                <Link to="/teacher/register" className="text-blue-600 font-semibold flex items-center hover:text-blue-700">
                  了解更多 <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                簡單三步驟，開始學習之旅
              </h2>
              <p className="text-xl text-gray-600">
                從註冊到看見成效，最快只需要一週
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl font-bold text-blue-600">1</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">教師註冊建立班級</h3>
                <p className="text-gray-600">
                  免費註冊帳號，建立班級並邀請學生加入，整個過程不到 5 分鐘
                </p>
              </div>

              <div className="text-center">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl font-bold text-blue-600">2</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">派發作業與練習</h3>
                <p className="text-gray-600">
                  從豐富的教材庫選擇，或自建課程內容，一鍵派發給全班學生
                </p>
              </div>

              <div className="text-center">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl font-bold text-blue-600">3</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">AI 評測與進度追蹤</h3>
                <p className="text-gray-600">
                  學生完成練習後，立即獲得 AI 回饋，教師可查看詳細學習報告
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                來自教育現場的真實回饋
              </h2>
              <p className="text-xl text-gray-600">
                看看其他教師和學生怎麼說
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <div className="bg-white rounded-2xl shadow-lg p-8">
                <div className="flex items-center mb-4">
                  {[1,2,3,4,5].map(i => (
                    <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <p className="text-gray-700 mb-6">
                  "Duotopia 讓我的學生愛上英語口說！AI 即時回饋功能太棒了，學生可以立即知道自己的發音問題。"
                </p>
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-indigo-400 rounded-full mr-4"></div>
                  <div>
                    <div className="font-semibold">王老師</div>
                    <div className="text-sm text-gray-600">台北市國小英語教師</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-lg p-8">
                <div className="flex items-center mb-4">
                  {[1,2,3,4,5].map(i => (
                    <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <p className="text-gray-700 mb-6">
                  "班級管理功能很完善，可以清楚看到每個學生的學習進度。省下很多批改作業的時間！"
                </p>
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-emerald-400 rounded-full mr-4"></div>
                  <div>
                    <div className="font-semibold">李老師</div>
                    <div className="text-sm text-gray-600">新竹市國中英語教師</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-lg p-8">
                <div className="flex items-center mb-4">
                  {[1,2,3,4,5].map(i => (
                    <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <p className="text-gray-700 mb-6">
                  "孩子每天都主動要練習英語，看到自己的進步很有成就感。感謝 Duotopia！"
                </p>
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full mr-4"></div>
                  <div>
                    <div className="font-semibold">陳家長</div>
                    <div className="text-sm text-gray-600">國小五年級學生家長</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-4xl font-bold mb-6">
              準備好革新您的英語教學了嗎？
            </h2>
            <p className="text-xl mb-8 text-blue-100">
              加入超過 1,000 位教師的行列，讓 AI 成為您的教學助手
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/teacher/register">
                <Button size="lg" className="bg-white text-blue-700 hover:bg-gray-100 px-8 py-6 text-lg font-semibold">
                  立即免費試用
                </Button>
              </Link>
              <Link to="/student/login">
                <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-blue-700 px-8 py-6 text-lg">
                  學生登入
                </Button>
              </Link>
            </div>
            <p className="mt-8 text-sm text-blue-200">
              無需信用卡 • 永久免費方案 • 5 分鐘快速上手
            </p>
          </div>
        </div>
      </section>

      {/* Login Options */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold text-center mb-8 text-gray-900">
              快速登入通道
            </h3>
            <div className="grid md:grid-cols-2 gap-6">
              {/* Teacher Login */}
              <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center mb-4">
                  <GraduationCap className="w-10 h-10 text-blue-600 mr-3" />
                  <h4 className="text-xl font-semibold">教師專區</h4>
                </div>
                <p className="text-gray-600 mb-4">
                  管理班級、建立課程、查看學習報告
                </p>
                <div className="space-y-2">
                  <Link to="/teacher/login" className="block">
                    <Button className="w-full">教師登入</Button>
                  </Link>
                  <Link to="/teacher/register" className="block">
                    <Button variant="outline" className="w-full">註冊新帳號</Button>
                  </Link>
                </div>
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-700 font-medium">Demo 帳號</p>
                  <p className="text-xs text-blue-600 mt-1">demo@duotopia.com / demo123</p>
                </div>
              </div>

              {/* Student Login */}
              <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center mb-4">
                  <Users className="w-10 h-10 text-green-600 mr-3" />
                  <h4 className="text-xl font-semibold">學生專區</h4>
                </div>
                <p className="text-gray-600 mb-4">
                  完成作業、練習口說、查看學習進度
                </p>
                <Link to="/student/login" className="block">
                  <Button className="w-full bg-green-600 hover:bg-green-700">
                    學生登入
                  </Button>
                </Link>
                <p className="text-sm text-gray-500 mt-3 text-center">
                  請使用教師提供的帳號密碼
                </p>
                <div className="mt-4 p-3 bg-green-50 rounded-lg">
                  <p className="text-xs text-green-700 font-medium">Demo 密碼</p>
                  <p className="text-xs text-green-600 mt-1">選擇學生後輸入: 20120101</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-4 gap-8">
              <div>
                <h3 className="text-white text-lg font-bold mb-4">Duotopia</h3>
                <p className="text-sm">
                  AI 驅動的多元智能英語學習平台，專為亞洲學生設計
                </p>
              </div>
              <div>
                <h4 className="text-white font-semibold mb-4">產品</h4>
                <ul className="space-y-2 text-sm">
                  <li><a href="#" className="hover:text-white">功能介紹</a></li>
                  <li><a href="#" className="hover:text-white">價格方案</a></li>
                  <li><a href="#" className="hover:text-white">更新日誌</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-white font-semibold mb-4">支援</h4>
                <ul className="space-y-2 text-sm">
                  <li><a href="#" className="hover:text-white">使用教學</a></li>
                  <li><a href="#" className="hover:text-white">常見問題</a></li>
                  <li><a href="#" className="hover:text-white">聯絡我們</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-white font-semibold mb-4">公司</h4>
                <ul className="space-y-2 text-sm">
                  <li><a href="#" className="hover:text-white">關於我們</a></li>
                  <li><a href="#" className="hover:text-white">隱私政策</a></li>
                  <li><a href="#" className="hover:text-white">使用條款</a></li>
                </ul>
              </div>
            </div>
            <div className="mt-8 pt-8 border-t border-gray-800 text-center text-sm">
              <p>&copy; 2024 Duotopia. All rights reserved.</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}