import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import {
  GraduationCap,
  Users,
  Mic,
  Brain,
  Trophy,
  BarChart3,
  Shield,
  Zap,
  ArrowRight,
  Play,
  CheckCircle,
  X,
  Puzzle,
  BookOpen,
  CheckSquare,
  Headphones,
} from "lucide-react";
import { DemoCard } from "@/components/DemoCard";
import { demoApi } from "@/lib/demoApi";
import { toast } from "sonner";

type DemoType =
  | "reading"
  | "rearrangement"
  | "vocabulary"
  | "wordSelectionListening"
  | "wordSelectionWriting";

interface DemoConfig {
  demo_reading_assignment_id?: string;
  demo_rearrangement_assignment_id?: string;
  demo_vocabulary_assignment_id?: string;
  demo_word_selection_listening_assignment_id?: string;
  demo_word_selection_writing_assignment_id?: string;
}

export default function Home() {
  const { t } = useTranslation();
  const isProduction = import.meta.env.PROD;
  const [isVideoModalOpen, setIsVideoModalOpen] = useState(false);

  // Demo section state
  const [demoConfig, setDemoConfig] = useState<DemoConfig | null>(null);

  // Fetch demo config on mount
  useEffect(() => {
    const fetchDemoConfig = async () => {
      try {
        const config = await demoApi.getConfig();
        setDemoConfig(config);
      } catch (error) {
        console.error("Failed to load demo config:", error);
        // Don't show error toast on homepage, just hide demo section
      }
    };

    fetchDemoConfig();
  }, []);

  // Open demo in new tab
  const openDemoInNewTab = (type: DemoType) => {
    if (!demoConfig) {
      toast.error(t("demo.configError"));
      return;
    }

    const assignmentIdMap: Record<DemoType, string | undefined> = {
      reading: demoConfig.demo_reading_assignment_id,
      rearrangement: demoConfig.demo_rearrangement_assignment_id,
      vocabulary: demoConfig.demo_vocabulary_assignment_id,
      wordSelectionListening:
        demoConfig.demo_word_selection_listening_assignment_id,
      wordSelectionWriting:
        demoConfig.demo_word_selection_writing_assignment_id,
    };

    const assignmentId = assignmentIdMap[type];
    if (!assignmentId) {
      toast.error(t("demo.notAvailable"));
      return;
    }

    window.open(`/demo/${assignmentId}`, "_blank");
  };

  return (
    <div className="min-h-screen bg-white">
      {/* 第一區段: Header - 白色背景 */}
      <header className="bg-white py-4 px-6 flex items-center justify-between shadow-sm">
        <img
          src="https://storage.googleapis.com/duotopia-social-media-videos/website/logo/logo_row_nobg.png"
          alt={t("home.header.logo")}
          className="h-10"
        />
        <LanguageSwitcher />
      </header>

      {/* 第二區段: Hero - 漸層背景 */}
      <section className="bg-gradient-to-b from-[#204dc0] to-[#101f6b] text-white py-20">
        <div className="container mx-auto px-4 sm:px-8 lg:px-16">
          <div className="grid lg:grid-cols-2 gap-8 xl:gap-10 min-[1440px]:gap-12 items-center max-w-6xl mx-auto">
            {/* 左側文案 */}
            <div>
              <p className="text-yellow-400 mb-2 text-base lg:text-lg font-medium">
                {t("home.hero.tagline")}
              </p>
              <h1 className="text-4xl lg:text-5xl min-[1440px]:text-6xl font-bold mb-4">
                {t("home.hero.brand")}
              </h1>
              <h2 className="text-xl lg:text-2xl min-[1440px]:text-3xl mb-6 text-blue-100">
                {t("home.hero.subtitle")}
              </h2>
              <p className="text-base lg:text-lg mb-4 leading-relaxed">
                {t("home.hero.description")}
              </p>
              <ul className="mb-8 space-y-2 text-blue-50">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>{t("home.hero.benefit1")}</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>{t("home.hero.benefit2")}</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>{t("home.hero.benefit3")}</span>
                </li>
              </ul>

              {/* 按鈕區域 */}
              <div className="flex flex-wrap gap-4 justify-center sm:justify-start">
                {/* 免費體驗按鈕 */}
                <Link to="/teacher/register">
                  <Button
                    size="lg"
                    className="bg-white text-gray-900 hover:bg-gray-100 px-8 py-6 text-lg font-semibold shadow-xl"
                  >
                    <img
                      src="https://storage.googleapis.com/duotopia-social-media-videos/website/assigment_icon.png"
                      alt=""
                      className="w-6 h-6 mr-2"
                    />
                    {t("home.hero.freeTrialBtn")}
                  </Button>
                </Link>

                {/* 觀看介紹影片按鈕 */}
                <Button
                  size="lg"
                  variant="outline"
                  className="border-2 border-white text-white hover:bg-white hover:text-blue-700 px-8 py-[22px] text-lg font-semibold transition-colors"
                  onClick={() => setIsVideoModalOpen(true)}
                >
                  <Play className="w-5 h-5 mr-2" />
                  {t("home.hero.watchVideo")}
                </Button>
              </div>

              {/* 教師頭像 + 統計 */}
              <div className="mt-8 flex flex-col sm:flex-row items-center gap-3 sm:gap-4 text-center sm:text-left">
                <div className="flex -space-x-3">
                  {[1, 2, 3, 4].map((i) => (
                    <img
                      key={i}
                      src={`https://storage.googleapis.com/duotopia-social-media-videos/website/teacherprofile_0${i}.png`}
                      alt={`Teacher ${i}`}
                      className="w-10 h-10 rounded-full border-2 border-white"
                    />
                  ))}
                </div>
                <div>
                  <p className="font-semibold text-sm sm:text-base">
                    {t("home.hero.trustedTeachers")}
                  </p>
                  <p className="text-blue-200 text-xs sm:text-sm">
                    {t("home.hero.studentsImproved")}
                  </p>
                </div>
              </div>
            </div>

            {/* 右側圖片 + 浮動徽章 */}
            <div className="hidden lg:flex lg:justify-end">
              <div className="relative inline-block">
                {/* 背景藍色區塊 - 跟隨圖片大小 */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl transform rotate-3 scale-105"></div>
                <img
                  src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600"
                  alt="Students learning"
                  className="relative rounded-2xl shadow-2xl max-w-[320px] xl:max-w-[400px] min-[1440px]:max-w-[500px] h-auto"
                />
                {/* 左下徽章 - AI 語音辨識 */}
                <div className="absolute -bottom-4 -left-4 bg-white rounded-xl shadow-xl p-3 flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900 text-sm">
                      AI 語音辨識
                    </div>
                    <div className="text-gray-500 text-xs">AI 語音辨識</div>
                  </div>
                </div>
                {/* 右上徽章 - 多元智能學習 */}
                <div className="absolute -top-4 -right-4 bg-white rounded-xl shadow-xl p-3 flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Brain className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900 text-sm">
                      多元智能學習
                    </div>
                    <div className="text-gray-500 text-xs">多元智能學習</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 第三區段: 快速登入 - #fafcfc 背景 */}
      <section className="py-16 bg-[#fafcfc]">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Teacher Login */}
              <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center mb-4">
                  <GraduationCap className="w-10 h-10 text-blue-600 mr-3" />
                  <h4 className="text-xl font-semibold">
                    {t("home.loginOptions.teacher.title")}
                  </h4>
                </div>
                <p className="text-gray-600 mb-4">
                  {t("home.loginOptions.teacher.description")}
                </p>
                <div className="space-y-2">
                  <Link to="/teacher/login" className="block">
                    <Button className="w-full">
                      {t("home.loginOptions.teacher.login")}
                    </Button>
                  </Link>
                  <Link to="/teacher/register" className="block">
                    <Button variant="outline" className="w-full">
                      {t("home.loginOptions.teacher.register")}
                    </Button>
                  </Link>
                </div>
                {/* Demo credentials - hidden in production */}
                {!isProduction && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-blue-700 font-medium">
                      {t("home.loginOptions.teacher.demoLabel")}
                    </p>
                    <p className="text-xs text-blue-600 mt-1">
                      {t("home.loginOptions.teacher.demoCredentials")}
                    </p>
                  </div>
                )}
              </div>

              {/* Student Login */}
              <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center mb-4">
                  <Users className="w-10 h-10 text-green-600 mr-3" />
                  <h4 className="text-xl font-semibold">
                    {t("home.loginOptions.student.title")}
                  </h4>
                </div>
                <p className="text-gray-600 mb-4">
                  {t("home.loginOptions.student.description")}
                </p>
                <Link to="/student/login" className="block">
                  <Button className="w-full bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600">
                    {t("home.loginOptions.student.login")}
                  </Button>
                </Link>
                <p className="text-sm text-gray-500 mt-3 text-center">
                  {t("home.loginOptions.student.note")}
                </p>
                {/* Demo credentials - hidden in production */}
                {!isProduction && (
                  <div className="mt-4 p-3 bg-green-50 rounded-lg">
                    <p className="text-xs text-green-700 font-medium">
                      {t("home.loginOptions.student.demoLabel")}
                    </p>
                    <p className="text-xs text-green-600 mt-1">
                      {t("home.loginOptions.student.demoPassword")}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Demo 體驗區 - 移到登入區下方 */}
      {demoConfig && (
        <section className="py-16 bg-gradient-to-b from-gray-50 to-white">
          <div className="container mx-auto px-4">
            <div className="max-w-6xl mx-auto">
              <div className="text-center mb-10">
                <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
                  {t("home.demo.title")}
                </h2>
                <p className="text-xl text-gray-600">
                  {t("home.demo.subtitle")}
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {/* 例句朗讀 */}
                <DemoCard
                  icon={<Mic className="h-7 w-7" />}
                  title={t("home.demo.reading.title")}
                  description={t("home.demo.reading.description")}
                  onClick={() => openDemoInNewTab("reading")}
                  gradient="from-blue-500 to-indigo-600"
                  disabled={!demoConfig.demo_reading_assignment_id}
                />

                {/* 例句重組 */}
                <DemoCard
                  icon={<Puzzle className="h-7 w-7" />}
                  title={t("home.demo.rearrangement.title")}
                  description={t("home.demo.rearrangement.description")}
                  onClick={() => openDemoInNewTab("rearrangement")}
                  gradient="from-green-500 to-emerald-600"
                  disabled={!demoConfig.demo_rearrangement_assignment_id}
                />

                {/* 單字朗讀 */}
                <DemoCard
                  icon={<BookOpen className="h-7 w-7" />}
                  title={t("home.demo.vocabulary.title")}
                  description={t("home.demo.vocabulary.description")}
                  onClick={() => openDemoInNewTab("vocabulary")}
                  gradient="from-purple-500 to-pink-600"
                  disabled={!demoConfig.demo_vocabulary_assignment_id}
                />

                {/* 單字聽力選擇 */}
                <DemoCard
                  icon={<Headphones className="h-7 w-7" />}
                  title={t("home.demo.wordSelectionListening.title")}
                  description={t(
                    "home.demo.wordSelectionListening.description",
                  )}
                  onClick={() => openDemoInNewTab("wordSelectionListening")}
                  gradient="from-orange-500 to-red-600"
                  disabled={
                    !demoConfig.demo_word_selection_listening_assignment_id
                  }
                />

                {/* 單字選擇 */}
                <DemoCard
                  icon={<CheckSquare className="h-7 w-7" />}
                  title={t("home.demo.wordSelectionWriting.title")}
                  description={t("home.demo.wordSelectionWriting.description")}
                  onClick={() => openDemoInNewTab("wordSelectionWriting")}
                  gradient="from-teal-500 to-cyan-600"
                  disabled={
                    !demoConfig.demo_word_selection_writing_assignment_id
                  }
                />
              </div>
            </div>
          </div>
        </section>
      )}

      {/* 第四區段: 為什麼選擇 Duotopia (保留原樣) */}
      <section className="py-20 lg:py-28">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                {t("home.features.title")}
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                {t("home.features.subtitle")}
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Mic className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">
                  {t("home.features.aiSpeech.title")}
                </h3>
                <p className="text-gray-600 mb-4">
                  {t("home.features.aiSpeech.description")}
                </p>
                <Link
                  to="/teacher/register"
                  className="text-blue-600 font-semibold flex items-center hover:text-blue-700"
                >
                  {t("home.features.learnMore")}{" "}
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>

              {/* Feature 2 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Brain className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">
                  {t("home.features.multiIntelligence.title")}
                </h3>
                <p className="text-gray-600 mb-4">
                  {t("home.features.multiIntelligence.description")}
                </p>
                <Link
                  to="/teacher/register"
                  className="text-blue-600 font-semibold flex items-center hover:text-blue-700"
                >
                  {t("home.features.learnMore")}{" "}
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>

              {/* Feature 3 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <BarChart3 className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">
                  {t("home.features.analytics.title")}
                </h3>
                <p className="text-gray-600 mb-4">
                  {t("home.features.analytics.description")}
                </p>
                <Link
                  to="/teacher/register"
                  className="text-blue-600 font-semibold flex items-center hover:text-blue-700"
                >
                  {t("home.features.learnMore")}{" "}
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>

              {/* Feature 4 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-orange-500 to-red-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Trophy className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">
                  {t("home.features.gamification.title")}
                </h3>
                <p className="text-gray-600 mb-4">
                  {t("home.features.gamification.description")}
                </p>
                <Link
                  to="/teacher/register"
                  className="text-blue-600 font-semibold flex items-center hover:text-blue-700"
                >
                  {t("home.features.learnMore")}{" "}
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>

              {/* Feature 5 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Shield className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">
                  {t("home.features.security.title")}
                </h3>
                <p className="text-gray-600 mb-4">
                  {t("home.features.security.description")}
                </p>
                <Link
                  to="/teacher/register"
                  className="text-blue-600 font-semibold flex items-center hover:text-blue-700"
                >
                  {t("home.features.learnMore")}{" "}
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>

              {/* Feature 6 */}
              <div className="group hover:shadow-xl transition-all duration-300 rounded-2xl p-8 border border-gray-100">
                <div className="w-14 h-14 bg-gradient-to-br from-teal-500 to-green-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Zap className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-3">
                  {t("home.features.easyToUse.title")}
                </h3>
                <p className="text-gray-600 mb-4">
                  {t("home.features.easyToUse.description")}
                </p>
                <Link
                  to="/teacher/register"
                  className="text-blue-600 font-semibold flex items-center hover:text-blue-700"
                >
                  {t("home.features.learnMore")}{" "}
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 第五區段: CTA - 漸層背景 */}
      <section className="bg-gradient-to-b from-[#204dc0] to-[#101f6b] text-white py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl lg:text-4xl font-bold mb-4">
              {t("home.cta2.title")}
            </h2>
            <p className="text-xl mb-10 text-blue-100">
              ✨ {t("home.cta2.subtitle")}
            </p>

            {/* 按鈕 + 教師頭像：大螢幕水平排列，小螢幕垂直排列 */}
            <div className="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-12">
              {/* 左側：按鈕 + 無須信用卡 */}
              <div className="flex flex-col items-center lg:items-end">
                <Link to="/teacher/register">
                  <Button
                    size="lg"
                    className="bg-white text-gray-900 hover:bg-gray-100 px-8 py-6 text-lg font-semibold shadow-xl"
                  >
                    <img
                      src="https://storage.googleapis.com/duotopia-social-media-videos/website/assigment_icon.png"
                      alt=""
                      className="w-6 h-6 mr-2"
                    />
                    {t("home.cta2.button")}
                  </Button>
                </Link>
                <p className="mt-3 text-sm text-blue-200">
                  {t("home.cta2.noCreditCard")}
                </p>
              </div>

              {/* 右側：教師頭像 + 統計 */}
              <div className="flex items-center gap-4">
                <div className="flex -space-x-3">
                  {[1, 2, 3, 4].map((i) => (
                    <img
                      key={i}
                      src={`https://storage.googleapis.com/duotopia-social-media-videos/website/teacherprofile_0${i}.png`}
                      alt={`Teacher ${i}`}
                      className="w-12 h-12 rounded-full border-2 border-white"
                    />
                  ))}
                </div>
                <div className="text-left">
                  <p className="font-semibold text-yellow-400">
                    {t("home.hero.trustedTeachers")}
                  </p>
                  <p className="text-blue-200 text-sm">
                    {t("home.hero.studentsImproved")}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 第六區段: 三步驟 */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl lg:text-4xl font-bold text-center mb-12 text-gray-900">
              {t("home.steps.title")}
            </h2>

            {/* 三個步驟圖示：小螢幕垂直排列，大螢幕水平排列 */}
            <div className="flex flex-col sm:flex-row justify-center items-center gap-8 sm:gap-12 lg:gap-16 mb-12">
              {/* 步驟 1 */}
              <div className="text-center">
                <img
                  src="https://storage.googleapis.com/duotopia-social-media-videos/website/sbs_icon01.png"
                  alt="Step 1"
                  className="w-20 h-20 mx-auto mb-4"
                />
                <p className="text-xl font-semibold text-gray-900">
                  {t("home.steps.step1")}
                </p>
              </div>

              {/* 步驟 2 */}
              <div className="text-center">
                <img
                  src="https://storage.googleapis.com/duotopia-social-media-videos/website/sbs_icon02.png"
                  alt="Step 2"
                  className="w-20 h-20 mx-auto mb-4"
                />
                <p className="text-xl font-semibold text-gray-900">
                  {t("home.steps.step2")}
                </p>
              </div>

              {/* 步驟 3 */}
              <div className="text-center">
                <img
                  src="https://storage.googleapis.com/duotopia-social-media-videos/website/sbs_icon03.png"
                  alt="Step 3"
                  className="w-20 h-20 mx-auto mb-4"
                />
                <p className="text-xl font-semibold text-gray-900">
                  {t("home.steps.step3")}
                </p>
              </div>
            </div>

            {/* 下方展示圖：小螢幕垂直排列，大螢幕水平排列 */}
            <div className="flex flex-col lg:flex-row justify-center gap-8 items-center">
              <img
                src="https://storage.googleapis.com/duotopia-social-media-videos/website/sbs_image01.png"
                alt="Demo 1"
                className="w-full max-w-sm lg:max-w-md rounded-xl shadow-lg"
              />
              <img
                src="https://storage.googleapis.com/duotopia-social-media-videos/website/sbs_image02.png"
                alt="Demo 2"
                className="w-full max-w-sm lg:max-w-md rounded-xl shadow-lg"
              />
            </div>
          </div>
        </div>
      </section>

      {/* 第七區段: Footer (保留原樣) */}
      <footer className="bg-gray-900 text-gray-300 py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-4 gap-8">
              <div>
                <h3 className="text-white text-lg font-bold mb-4">
                  {t("home.hero.brand")}
                </h3>
                <p className="text-sm mb-4">{t("home.footer.description")}</p>
                <div className="text-sm">
                  <p className="text-gray-400 mb-1">
                    {t("home.footer.contact")}
                  </p>
                  <a
                    href="mailto:contact@duotopia.co"
                    className="text-blue-400 hover:text-blue-300"
                  >
                    contact@duotopia.co
                  </a>
                </div>
              </div>
              <div>
                <h4 className="text-white font-semibold mb-4">
                  {t("home.footer.product")}
                </h4>
                <ul className="space-y-2 text-sm">
                  <li>
                    <a href="#" className="hover:text-white">
                      {t("home.footer.features")}
                    </a>
                  </li>
                  <li>
                    <Link to="/pricing" className="hover:text-white">
                      {t("home.footer.pricing")}
                    </Link>
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="text-white font-semibold mb-4">
                  {t("home.footer.support")}
                </h4>
                <ul className="space-y-2 text-sm">
                  <li>
                    <a href="#" className="hover:text-white">
                      {t("home.footer.tutorial")}
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-white">
                      {t("home.footer.faq")}
                    </a>
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="text-white font-semibold mb-4">
                  {t("home.footer.company")}
                </h4>
                <ul className="space-y-2 text-sm">
                  <li>
                    <a href="#" className="hover:text-white">
                      {t("home.footer.about")}
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-white">
                      {t("home.footer.privacy")}
                    </a>
                  </li>
                  <li>
                    <Link to="/terms" className="hover:text-white">
                      {t("home.footer.terms")}
                    </Link>
                  </li>
                </ul>
              </div>
            </div>
            <div className="mt-8 pt-8 border-t border-gray-800 text-center text-sm">
              <p>{t("home.footer.copyright")}</p>
            </div>
          </div>
        </div>
      </footer>

      {/* 影片彈窗 Modal */}
      {isVideoModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
          onClick={() => setIsVideoModalOpen(false)}
        >
          <div
            className="relative w-full max-w-4xl mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 關閉按鈕 */}
            <button
              onClick={() => setIsVideoModalOpen(false)}
              className="absolute -top-12 right-0 text-white hover:text-gray-300 transition-colors"
              aria-label="Close video"
            >
              <X className="w-8 h-8" />
            </button>

            {/* YouTube 影片嵌入 */}
            <div className="relative pt-[56.25%] bg-black rounded-lg overflow-hidden">
              <iframe
                className="absolute inset-0 w-full h-full"
                src="https://www.youtube.com/embed/m2jfog0EvXo?list=PLu97PbZuQSs0nK6raEQmCj5Fj_0YxExt2&autoplay=1"
                title="Duotopia 介紹影片"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
