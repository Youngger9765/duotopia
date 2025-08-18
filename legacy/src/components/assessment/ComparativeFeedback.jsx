import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Sparkles } from "lucide-react";

export default function ComparativeFeedback({ feedback }) {
  if (!feedback) return null;

  return (
    <Card className="bg-gradient-to-r from-teal-50 to-blue-50 border-teal-200">
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-teal-500 rounded-full flex items-center justify-center text-white flex-shrink-0">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h4 className="font-bold text-teal-800 text-lg mb-1">AI 學習教練</h4>
            <p className="text-teal-700">{feedback}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}