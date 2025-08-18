import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Edit, Trash2, Target, Mail, BarChart3 } from 'lucide-react';
import { createPageUrl } from "@/utils";
import { Link } from "react-router-dom";

export default function MobileStudentCard({ student, onEditStudent, onDeleteStudent }) {
  return (
    <Card className="bg-white/90 shadow-md">
      <CardContent className="p-4 space-y-3">
        <div className="flex justify-between items-start">
          <div>
            <h4 className="font-bold text-gray-900">{student.student_name}</h4>
            <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
              <Mail className="w-3 h-3" />
              {student.email}
            </p>
          </div>
          <Badge variant="outline">{student.student_id}</Badge>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm border-t pt-3">
          <div className="flex items-center gap-1">
            <Target className="w-4 h-4 text-blue-500" />
            <div>
              <p className="text-xs text-gray-500">目標WPM</p>
              <p className="font-medium">{student.target_wpm}</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Target className="w-4 h-4 text-green-500" />
              <div>
              <p className="text-xs text-gray-500">目標正確率</p>
              <p className="font-medium">{student.target_accuracy}%</p>
            </div>
          </div>
        </div>
        {student.tags && student.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 border-t pt-3">
            {student.tags.map(tag => <Badge key={tag} variant="secondary">{tag}</Badge>)}
          </div>
        )}
        <div className="flex gap-2 pt-3 border-t">
          <Link to={createPageUrl(`Statistics?view_mode=teacher&student_email=${student.email}`)} className="flex-1">
            <Button variant="outline" size="sm" className="w-full">
              <BarChart3 className="w-3 h-3 mr-1" />
              報告
            </Button>
          </Link>
          <Button variant="outline" size="sm" onClick={onEditStudent} className="flex-1">
            <Edit className="w-3 h-3 mr-1" /> 編輯
          </Button>
          <Button variant="destructive" size="sm" onClick={onDeleteStudent} className="flex-1">
            <Trash2 className="w-3 h-3 mr-1" /> 刪除
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}