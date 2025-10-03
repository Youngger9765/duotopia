import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, Users, Star } from 'lucide-react';

interface PricingPlan {
  name: string;
  description: string;
  studentRange: string;
  monthlyPrice: number;
  features: string[];
  popular?: boolean;
}

export default function PricingPage() {
  const pricingPlans: PricingPlan[] = [
    {
      name: "Tutor Teachers",
      description: "小型家教ESL教師",
      studentRange: "1-100人",
      monthlyPrice: 230,
      features: [
        "支援 1-100 位學生",
        "完整功能使用權",
        "標準客服支援"
      ]
    },
    {
      name: "School Teachers",
      description: "校園ESL教師",
      studentRange: "101-200人",
      monthlyPrice: 330,
      features: [
        "支援 101-200 位學生",
        "完整功能使用權",
        "優先客服支援"
      ],
      popular: true
    }
  ];


  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-12">
      <div className="container mx-auto px-4">
        {/* Header Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            選擇適合您的方案
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            專為ESL教師設計的教學管理平台
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="max-w-4xl mx-auto">
          <div className="grid md:grid-cols-2 gap-8">
            {pricingPlans.map((plan, index) => {
              return (
                <Card
                  key={index}
                  className={`relative p-8 hover:shadow-xl transition-all duration-300 ${
                    plan.popular ? 'border-blue-500 border-2 scale-105' : ''
                  }`}
                >
                  {plan.popular && (
                    <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white">
                      <Star className="w-3 h-3 mr-1" />
                      熱門選擇
                    </Badge>
                  )}

                  <div className="text-center mb-6">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">
                      {plan.name}
                    </h3>
                    <p className="text-gray-600">{plan.description}</p>
                    <div className="flex items-center justify-center mt-3 text-gray-500">
                      <Users className="w-4 h-4 mr-2" />
                      <span>學生人數: {plan.studentRange}</span>
                    </div>
                  </div>

                  {/* 價格區塊 */}
                  <div className="mb-8">
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">月付方案</span>
                        <div className="text-right">
                          <span className="text-3xl font-bold text-gray-900">
                            NT$ {plan.monthlyPrice}
                          </span>
                          <span className="text-gray-600 ml-1">/月</span>
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
                    className={`w-full ${
                      plan.popular
                        ? 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600'
                        : 'bg-gray-800 hover:bg-gray-900 dark:bg-gray-700 dark:hover:bg-gray-800'
                    } text-white`}
                  >
                    立即訂閱
                  </Button>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Bottom Info */}
        <div className="mt-16 text-center">
          <div className="bg-white rounded-lg p-6 max-w-2xl mx-auto shadow-md">
            <h3 className="font-semibold text-gray-900 mb-3">付費方案說明</h3>
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-900 mb-1">月付方案</p>
              <p>按月計費，彈性調整，隨時升級或調整您的方案</p>
            </div>
          </div>

          <div className="mt-8">
            <p className="text-gray-600 mb-4">
              需要更多學生數量或自訂方案？
            </p>
            <p className="text-gray-900 font-medium">
              請聯絡：<a href="mailto:myduotopia@gmail.com" className="text-blue-600 hover:text-blue-700 underline">myduotopia@gmail.com</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
