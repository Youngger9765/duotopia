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
} from "lucide-react";

export default function Home() {
  const { t } = useTranslation();

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
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* 左側文案 */}
            <div>
              <p className="text-yellow-400 mb-2 text-lg font-medium">
                {t("home.hero.tagline")}
              </p>
              <h1 className="text-5xl lg:text-6xl font-bold mb-4">
                {t("home.hero.brand")}
              </h1>
              <h2 className="text-2xl lg:text-3xl mb-6 text-blue-100">
                {t("home.hero.subtitle")}
              </h2>
              <p className="text-lg mb-4 leading-relaxed">
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

              {/* 免費體驗按鈕 */}
              <Link to="/teacher/register">
                <Button
                  size="lg"
                  className="bg-yellow-400 text-black hover:bg-yellow-300 px-8 py-6 text-lg font-semibold shadow-xl"
                >
                  <img
                    src="https://storage.googleapis.com/duotopia-social-media-videos/website/assigment_icon.png"
                    alt=""
                    className="w-6 h-6 mr-2"
                  />
                  {t("home.hero.freeTrialBtn")}
                </Button>
              </Link>

              {/* 教師頭像 + 統計 */}
              <div className="mt-8 flex items-center gap-4">
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
                  <p className="font-semibold">
                    {t("home.hero.trustedTeachers")}
                  </p>
                  <p className="text-blue-200 text-sm">
                    {t("home.hero.studentsImproved")}
                  </p>
                </div>
              </div>
            </div>

            {/* 右側影片 */}
            <div className="flex justify-center lg:justify-end">
              <iframe
                width="315"
                height="560"
                src="https://www.youtube.com/embed/neansyCiT6Q"
                title="Duotopia Demo"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="rounded-xl shadow-2xl"
              />
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
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-700 font-medium">
                    {t("home.loginOptions.teacher.demoLabel")}
                  </p>
                  <p className="text-xs text-blue-600 mt-1">
                    {t("home.loginOptions.teacher.demoCredentials")}
                  </p>
                </div>
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
                <div className="mt-4 p-3 bg-green-50 rounded-lg">
                  <p className="text-xs text-green-700 font-medium">
                    {t("home.loginOptions.student.demoLabel")}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    {t("home.loginOptions.student.demoPassword")}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

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
                    href="mailto:myduotopia@gmail.com"
                    className="text-blue-400 hover:text-blue-300"
                  >
                    myduotopia@gmail.com
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
    </div>
  );
}
