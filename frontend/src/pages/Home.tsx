import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import {
  GraduationCap,
  Users,
  Sparkles,
  Brain,
  Mic,
  Trophy,
  BarChart3,
  Shield,
  Zap,
  CheckCircle,
  ArrowRight,
  Play,
  Star,
} from "lucide-react";

export default function Home() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-white">
      {/* Language Switcher - Fixed in top right */}
      <div className="fixed top-4 right-4 z-50">
        <LanguageSwitcher />
      </div>

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
                  <span className="text-yellow-400 font-semibold">
                    {t("home.hero.badge")}
                  </span>
                </div>
                <h1 className="text-5xl lg:text-6xl font-bold mb-6 leading-tight">
                  {t("home.hero.title")}
                  <span className="block text-3xl lg:text-4xl mt-2 text-blue-200">
                    {t("home.hero.subtitle")}
                  </span>
                </h1>
                <p className="text-xl mb-8 text-blue-100 leading-relaxed">
                  {t("home.hero.description")}
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link to="/teacher/register">
                    <Button
                      size="lg"
                      className="bg-white text-blue-700 hover:bg-gray-100 px-8 py-6 text-lg font-semibold shadow-xl"
                    >
                      <GraduationCap className="mr-2 h-5 w-5" />
                      {t("home.hero.freeTrial")}
                    </Button>
                  </Link>
                  <Button
                    size="lg"
                    variant="outline"
                    className="border-2 border-white/80 text-white bg-white/10 backdrop-blur-sm hover:bg-white hover:text-blue-700 px-8 py-6 text-lg font-semibold transition-all"
                  >
                    <Play className="mr-2 h-5 w-5" />
                    {t("home.hero.watchVideo")}
                  </Button>
                </div>
                <div className="mt-8 flex items-center space-x-6">
                  <div className="flex -space-x-2">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className="w-10 h-10 bg-gradient-to-br from-blue-400 to-indigo-400 rounded-full border-2 border-white"
                      ></div>
                    ))}
                  </div>
                  <div className="text-sm">
                    <div className="font-semibold">
                      {t("home.hero.trustedBy").replace("{{count}}", "1,000")}
                    </div>
                    <div className="text-blue-200">
                      {t("home.hero.studentsUsing").replace(
                        "{{count}}",
                        "10,000",
                      )}
                    </div>
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
                      <div className="font-semibold text-gray-900">
                        {t("home.features.aiSpeech.title")}
                      </div>
                      <div className="text-sm text-gray-600">
                        {t("home.features.aiSpeech.title")}
                      </div>
                    </div>
                  </div>
                  <div className="absolute -top-6 -right-6 bg-white rounded-xl shadow-xl p-4 flex items-center space-x-3">
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <Brain className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">
                        {t("home.features.multiIntelligence.title")}
                      </div>
                      <div className="text-sm text-gray-600">
                        {t("home.features.multiIntelligence.title")}
                      </div>
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
                <div className="text-sm text-gray-600 mt-1">
                  {t("home.stats.satisfaction")}
                </div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">
                  3{t("home.stats.improvementTime")}
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  {t("home.stats.improvementTime")}
                </div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">50%</div>
                <div className="text-sm text-gray-600 mt-1">
                  {t("home.stats.speakingImprovement")}
                </div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">24/7</div>
                <div className="text-sm text-gray-600 mt-1">
                  {t("home.stats.availability")}
                </div>
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

      {/* How it Works */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                {t("home.howItWorks.title")}
              </h2>
              <p className="text-xl text-gray-600">
                {t("home.howItWorks.subtitle")}
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl font-bold text-blue-600">1</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">
                  {t("home.howItWorks.step1.title")}
                </h3>
                <p className="text-gray-600">
                  {t("home.howItWorks.step1.description")}
                </p>
              </div>

              <div className="text-center">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl font-bold text-blue-600">2</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">
                  {t("home.howItWorks.step2.title")}
                </h3>
                <p className="text-gray-600">
                  {t("home.howItWorks.step2.description")}
                </p>
              </div>

              <div className="text-center">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl font-bold text-blue-600">3</span>
                </div>
                <h3 className="text-xl font-semibold mb-3">
                  {t("home.howItWorks.step3.title")}
                </h3>
                <p className="text-gray-600">
                  {t("home.howItWorks.step3.description")}
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
                {t("home.testimonials.title")}
              </h2>
              <p className="text-xl text-gray-600">
                {t("home.testimonials.subtitle")}
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <div className="bg-white rounded-2xl shadow-lg p-8">
                <div className="flex items-center mb-4">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Star
                      key={i}
                      className="h-5 w-5 fill-yellow-400 text-yellow-400"
                    />
                  ))}
                </div>
                <p className="text-gray-700 mb-6">
                  {t("home.testimonials.teacher1.quote")}
                </p>
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-indigo-400 rounded-full mr-4"></div>
                  <div>
                    <div className="font-semibold">
                      {t("home.testimonials.teacher1.name")}
                    </div>
                    <div className="text-sm text-gray-600">
                      {t("home.testimonials.teacher1.role")}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-lg p-8">
                <div className="flex items-center mb-4">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Star
                      key={i}
                      className="h-5 w-5 fill-yellow-400 text-yellow-400"
                    />
                  ))}
                </div>
                <p className="text-gray-700 mb-6">
                  {t("home.testimonials.teacher2.quote")}
                </p>
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-emerald-400 rounded-full mr-4"></div>
                  <div>
                    <div className="font-semibold">
                      {t("home.testimonials.teacher2.name")}
                    </div>
                    <div className="text-sm text-gray-600">
                      {t("home.testimonials.teacher2.role")}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-lg p-8">
                <div className="flex items-center mb-4">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Star
                      key={i}
                      className="h-5 w-5 fill-yellow-400 text-yellow-400"
                    />
                  ))}
                </div>
                <p className="text-gray-700 mb-6">
                  {t("home.testimonials.parent1.quote")}
                </p>
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full mr-4"></div>
                  <div>
                    <div className="font-semibold">
                      {t("home.testimonials.parent1.name")}
                    </div>
                    <div className="text-sm text-gray-600">
                      {t("home.testimonials.parent1.role")}
                    </div>
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
            <h2 className="text-4xl font-bold mb-6">{t("home.cta.title")}</h2>
            <p className="text-xl mb-8 text-blue-100">
              {t("home.cta.subtitle").replace("{{count}}", "1,000")}
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/teacher/register">
                <Button
                  size="lg"
                  className="bg-white text-blue-700 hover:bg-gray-100 px-8 py-6 text-lg font-semibold"
                >
                  {t("home.cta.startFreeTrial")}
                </Button>
              </Link>
              <Link to="/student/login">
                <Button
                  size="lg"
                  variant="outline"
                  className="border-2 border-white/80 text-white bg-white/10 backdrop-blur-sm hover:bg-white hover:text-blue-700 px-8 py-6 text-lg font-semibold transition-all"
                >
                  {t("home.cta.studentLogin")}
                </Button>
              </Link>
            </div>
            <p className="mt-8 text-sm text-blue-200">
              {t("home.cta.benefits")}
            </p>
          </div>
        </div>
      </section>

      {/* Login Options */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold text-center mb-8 text-gray-900">
              {t("home.loginOptions.title")}
            </h3>
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

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-4 gap-8">
              <div>
                <h3 className="text-white text-lg font-bold mb-4">
                  {t("home.hero.title")}
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
