import React from "react";
import { Check } from "lucide-react";

interface SubscriptionProgressBannerProps {
  currentStep: "select-plan" | "login" | "payment" | "complete";
  selectedPlan?: string;
}

export default function SubscriptionProgressBanner({
  currentStep,
  selectedPlan,
}: SubscriptionProgressBannerProps) {
  const steps = [
    { id: "select-plan", label: "選擇方案", icon: "1" },
    { id: "login", label: "登入帳號", icon: "2" },
    { id: "payment", label: "填寫付款資訊", icon: "3" },
    { id: "complete", label: "完成訂閱", icon: "4" },
  ];

  const getStepStatus = (stepId: string) => {
    const currentIndex = steps.findIndex((s) => s.id === currentStep);
    const stepIndex = steps.findIndex((s) => s.id === stepId);

    if (stepIndex < currentIndex) return "completed";
    if (stepIndex === currentIndex) return "active";
    return "pending";
  };

  return (
    <div className="bg-blue-50 border-b border-blue-200 px-4 py-3">
      <div className="container mx-auto max-w-4xl">
        {selectedPlan && (
          <div className="text-center mb-3">
            <span className="text-sm text-blue-700">
              正在訂閱: <strong>{selectedPlan}</strong>
            </span>
          </div>
        )}

        <div className="flex items-center justify-between">
          {steps.map((step, index) => {
            const status = getStepStatus(step.id);
            const isLast = index === steps.length - 1;

            return (
              <React.Fragment key={step.id}>
                <div className="flex flex-col items-center">
                  <div className="flex items-center">
                    <div
                      className={`
                        w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm
                        ${
                          status === "completed"
                            ? "bg-green-500 text-white"
                            : status === "active"
                              ? "bg-blue-600 text-white ring-4 ring-blue-200"
                              : "bg-gray-300 text-gray-600"
                        }
                      `}
                    >
                      {status === "completed" ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <span>{step.icon}</span>
                      )}
                    </div>
                  </div>
                  <span
                    className={`
                      text-xs mt-2 font-medium whitespace-nowrap
                      ${
                        status === "active"
                          ? "text-blue-700"
                          : status === "completed"
                            ? "text-green-700"
                            : "text-gray-500"
                      }
                    `}
                  >
                    {step.label}
                  </span>
                </div>

                {!isLast && (
                  <div className="flex-1 mx-2">
                    <div className="h-1 bg-gray-300 rounded">
                      <div
                        className={`h-full rounded transition-all duration-500 ${
                          status === "completed" ? "bg-green-500 w-full" : "w-0"
                        }`}
                      />
                    </div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
