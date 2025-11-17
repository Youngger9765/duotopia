import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Check,
  Users,
  Star,
  CreditCard,
  Shield,
  User,
  LogOut,
  LogIn,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import TapPayPayment from "@/components/payment/TapPayPayment";
import TeacherLoginModal from "@/components/TeacherLoginModal";
import { toast } from "sonner";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useStudentAuthStore } from "@/stores/studentAuthStore";

interface PricingPlan {
  id: string;
  name: string;
  description: string;
  studentRange: string;
  monthlyPrice: number;
  features: string[];
  popular?: boolean;
}

export default function PricingPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [selectedPlan, setSelectedPlan] = useState<PricingPlan | null>(null);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [userInfo, setUserInfo] = useState<{
    isLoggedIn: boolean;
    name?: string;
    email?: string;
    role?: string;
  } | null>(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [pendingPlan, setPendingPlan] = useState<PricingPlan | null>(null);
  const pricingPlans: PricingPlan[] = [
    {
      id: "tutor",
      name: "Tutor Teachers",
      description: "小型家教ESL教師",
      studentRange: "1-100人",
      monthlyPrice: 330,
      features: [
        "10000 點配額/月（錄音、評分、文字批改）",
        "支援 1-100 位學生",
        "無限制派發作業（不扣配額）",
        "AI 語音評估與批改",
        "完整功能使用權",
        "標準客服支援",
        "學習進度追蹤",
      ],
    },
    {
      id: "school",
      name: "School Teachers",
      description: "校園ESL教師",
      studentRange: "101-200人",
      monthlyPrice: 660,
      features: [
        "25000 點配額/月（錄音、評分、文字批改）",
        "支援 101-200 位學生",
        "無限制派發作業（不扣配額）",
        "AI 語音評估與批改",
        "完整功能使用權",
        "優先客服支援",
        "進階數據分析",
        "多班級管理",
        "批次作業指派",
      ],
      popular: true,
    },
  ];

  const handleSelectPlan = (plan: PricingPlan) => {
    const teacherAuth = useTeacherAuthStore.getState();
    const studentAuth = useStudentAuthStore.getState();

    // User is not logged in
    if (!teacherAuth.isAuthenticated) {
      // Store the plan and open login modal
      setPendingPlan(plan);
      setShowLoginModal(true);
      toast.info(t("pricing.actions.loginRequired"));
      return;
    }

    // Check if a student is logged in instead
    if (studentAuth.isAuthenticated) {
      toast.error(t("pricing.actions.studentAccountWarning"));
      return;
    }

    setSelectedPlan(plan);
    setShowPaymentDialog(true);
  };

  const handlePaymentSuccess = async (transactionId: string) => {
    try {
      // Mock API call - will be replaced with real API
      console.log("Payment successful, transaction ID:", transactionId);
      toast.success(
        t("pricing.payment.success", { planName: selectedPlan?.name }),
      );
      setShowPaymentDialog(false);
      // Navigate to dashboard after successful payment
      setTimeout(() => {
        navigate("/teacher/dashboard");
      }, 2000);
    } catch (error) {
      console.error("Payment error:", error);
      toast.error(t("pricing.payment.error"));
    }
  };

  const handlePaymentError = (error: string) => {
    // 🎉 檢查是否為免費優惠期間提醒
    if (error.includes("免費優惠期間") || error.includes("未來將會開放儲值")) {
      toast.info(error, {
        duration: 6000,
      });
      // 關閉付款對話框
      setShowPaymentDialog(false);
    } else {
      toast.error(t("pricing.payment.failed", { error }));
    }
  };

  // Check user login status and subscription
  useEffect(() => {
    checkUserStatus();
    checkSubscriptionStatus();
  }, []);

  const checkUserStatus = () => {
    // Use stores instead of localStorage
    const teacherAuth = useTeacherAuthStore.getState();
    const studentAuth = useStudentAuthStore.getState();

    if (teacherAuth.isAuthenticated && teacherAuth.user) {
      setUserInfo({
        isLoggedIn: true,
        name:
          teacherAuth.user.name ||
          teacherAuth.user.email?.split("@")[0] ||
          "教師",
        email: teacherAuth.user.email,
        role: "teacher",
      });
    } else if (studentAuth.isAuthenticated && studentAuth.user) {
      setUserInfo({
        isLoggedIn: true,
        name: studentAuth.user.name || `學生 ${studentAuth.user.id}`,
        email: studentAuth.user.email,
        role: "student",
      });
    } else {
      setUserInfo({ isLoggedIn: false });
    }
  };

  const checkSubscriptionStatus = async () => {
    const teacherAuth = useTeacherAuthStore.getState();
    if (!teacherAuth.isAuthenticated || !teacherAuth.token) return;

    try {
      // Check if user has active subscription
      const apiUrl = import.meta.env.VITE_API_URL;
      const response = await fetch(`${apiUrl}/subscription/status`, {
        headers: {
          Authorization: `Bearer ${teacherAuth.token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        // If user has active subscription, redirect to subscription management
        if (data.is_active) {
          toast.info(t("pricing.payment.hasSubscription"));
          setTimeout(() => {
            navigate("/teacher/subscription");
          }, 1000);
        }
      }
    } catch (error) {
      console.error("Error checking subscription:", error);
    }
  };

  const handleLogout = () => {
    // Clear all auth data
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("teacher-auth-storage");
    localStorage.removeItem("student-auth-storage");
    localStorage.removeItem("auth-storage");
    localStorage.removeItem("user");
    localStorage.removeItem("role");
    localStorage.removeItem("username");
    localStorage.removeItem("userType");
    localStorage.removeItem("selectedPlan");

    setUserInfo({ isLoggedIn: false });
    toast.success(t("common.success"));
  };

  // Check if user came back from login with a selected plan
  useEffect(() => {
    const savedPlan = localStorage.getItem("selectedPlan");

    if (savedPlan && userInfo?.isLoggedIn && userInfo?.role === "teacher") {
      try {
        const planData = JSON.parse(savedPlan);
        const plan = pricingPlans.find((p) => p.id === planData.id);
        if (plan) {
          // Auto-open payment dialog for returning users
          setSelectedPlan(plan);
          setShowPaymentDialog(true);
          // Clear the saved plan
          localStorage.removeItem("selectedPlan");
          toast.success(t("pricing.payment.redirecting"));
        }
      } catch (error) {
        console.error("Error parsing saved plan:", error);
      }
    }
  }, [pricingPlans, userInfo]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* User Status Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b dark:border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
            {/* Logo Section */}
            <div className="flex items-center gap-2 sm:gap-4">
              <Link
                to="/"
                className="text-xl sm:text-2xl font-bold text-blue-600 dark:text-blue-400"
              >
                {t("pricing.header.logo")}
              </Link>
              <span className="text-gray-400 dark:text-gray-500 hidden sm:inline">
                |
              </span>
              <span className="text-sm sm:text-base text-gray-600 dark:text-gray-300">
                {t("pricing.title")}
              </span>
            </div>

            {/* User Actions */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4">
              {userInfo?.isLoggedIn ? (
                <>
                  {/* User Info */}
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600 dark:text-gray-300" />
                    <div className="text-left sm:text-right">
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {userInfo.name}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {userInfo.role === "teacher"
                          ? t("pricing.header.teacherAccount")
                          : t("pricing.header.studentAccount")}
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 w-full sm:w-auto">
                    {userInfo.role === "teacher" ? (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate("/teacher/dashboard")}
                        className="flex-1 sm:flex-none"
                      >
                        {t("pricing.header.backToDashboard")}
                      </Button>
                    ) : (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate("/student/dashboard")}
                        className="flex-1 sm:flex-none"
                      >
                        {t("pricing.header.backToStudentArea")}
                      </Button>
                    )}

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleLogout}
                      className="flex-1 sm:flex-none"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      {t("nav.logout")}
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => setShowLoginModal(true)}
                    className="w-full sm:w-auto"
                  >
                    <LogIn className="w-4 h-4 mr-2" />
                    {t("pricing.header.teacherLogin")}
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-12">
        {/* Header Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {t("pricing.subtitle")}
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            {t("pricing.description")}
          </p>

          {userInfo?.isLoggedIn && userInfo.role === "student" && (
            <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 max-w-md mx-auto">
              <p className="text-sm text-yellow-800">
                ⚠️ {t("pricing.actions.studentAccountWarning")}
              </p>
            </div>
          )}
        </div>

        {/* Pricing Cards */}
        <div className="max-w-4xl mx-auto">
          <div className="grid md:grid-cols-2 gap-8">
            {pricingPlans.map((plan, index) => {
              return (
                <Card
                  key={index}
                  className={`relative p-8 hover:shadow-xl transition-all duration-300 ${
                    plan.popular ? "border-blue-500 border-2 scale-105" : ""
                  }`}
                >
                  {plan.popular && (
                    <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white">
                      <Star className="w-3 h-3 mr-1" />
                      {t("pricing.schoolPlan.popular")}
                    </Badge>
                  )}

                  <div className="text-center mb-6">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">
                      {plan.name}
                    </h3>
                    <p className="text-gray-600">{plan.description}</p>
                    <div className="flex items-center justify-center mt-3 text-gray-500">
                      <Users className="w-4 h-4 mr-2" />
                      <span>{plan.studentRange}</span>
                    </div>
                  </div>

                  {/* 價格區塊 */}
                  <div className="mb-8">
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">
                          {t("pricing.billing.monthly")}
                        </span>
                        <div className="text-right">
                          <span className="text-3xl font-bold text-gray-900">
                            NT$ {plan.monthlyPrice}
                          </span>
                          <span className="text-gray-600 ml-1">
                            {t("pricing.billing.perMonth")}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start">
                        <Check className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Button
                    onClick={() => handleSelectPlan(plan)}
                    disabled={userInfo?.role === "student"}
                    className={`w-full ${
                      userInfo?.role === "student"
                        ? "bg-gray-300 cursor-not-allowed text-gray-500"
                        : plan.popular
                          ? "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white"
                          : "bg-gray-800 hover:bg-gray-900 dark:bg-gray-700 dark:hover:bg-gray-800 text-white"
                    }`}
                  >
                    <CreditCard className="mr-2 h-4 w-4" />
                    {userInfo?.role === "student"
                      ? t("pricing.actions.studentCannotSubscribe")
                      : t("pricing.actions.subscribe")}
                  </Button>

                  {userInfo?.role === "student" && (
                    <p className="text-xs text-red-500 mt-2 text-center">
                      {t("pricing.actions.logoutFirst")}
                    </p>
                  )}
                </Card>
              );
            })}
          </div>
        </div>

        {/* Bottom Info */}
        <div className="mt-16 text-center">
          <div className="bg-white rounded-lg p-6 max-w-2xl mx-auto shadow-md">
            <h3 className="font-semibold text-gray-900 mb-3">
              {t("pricing.billing.monthly")}
            </h3>
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-900 mb-1">
                {t("pricing.billing.monthly")}
              </p>
              <p>{t("pricing.billing.description")}</p>
            </div>
          </div>

          <div className="mt-8">
            <p className="text-gray-600 mb-4">{t("pricing.needMore")}</p>
            <p className="text-gray-900 font-medium">
              {t("pricing.contactUs")}
              <a
                href="mailto:myduotopia@gmail.com"
                className="text-blue-600 hover:text-blue-700 underline"
              >
                myduotopia@gmail.com
              </a>
            </p>
          </div>
        </div>
      </div>

      {/* Payment Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{t("pricing.payment.title")}</DialogTitle>
            <DialogDescription className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-green-600" />
              {t("pricing.payment.securePayment")} -{" "}
              {t("pricing.payment.selectedPlan", {
                planName: selectedPlan?.name,
              })}
            </DialogDescription>
          </DialogHeader>

          {selectedPlan && (
            <TapPayPayment
              amount={selectedPlan.monthlyPrice}
              planName={selectedPlan.name}
              onPaymentSuccess={handlePaymentSuccess}
              onPaymentError={handlePaymentError}
              onCancel={() => setShowPaymentDialog(false)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Login Modal */}
      <TeacherLoginModal
        isOpen={showLoginModal}
        onClose={() => {
          setShowLoginModal(false);
          setPendingPlan(null);
        }}
        onLoginSuccess={() => {
          // Update user status immediately after login
          checkUserStatus();
          setShowLoginModal(false);

          // Small delay to ensure state is updated
          setTimeout(() => {
            // If there was a pending plan, open payment dialog
            if (pendingPlan) {
              setSelectedPlan(pendingPlan);
              setShowPaymentDialog(true);
              setPendingPlan(null);
            }
          }, 100);
        }}
        selectedPlan={pendingPlan || undefined}
      />
    </div>
  );
}
