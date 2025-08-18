
import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, Filter, X, Tag } from "lucide-react";
import { ClassStudent } from "@/api/entities";
import { Class } from "@/api/entities";

const TAG_COLORS = {
  "需關注": "bg-red-100 text-red-800 border-red-200",
  "朗讀困難": "bg-orange-100 text-orange-800 border-orange-200", 
  "優秀": "bg-green-100 text-green-800 border-green-200",
  "進步中": "bg-blue-100 text-blue-800 border-blue-200",
  "特教生": "bg-purple-100 text-purple-800 border-purple-200",
  "新生": "bg-yellow-100 text-yellow-800 border-yellow-200",
  "轉學生": "bg-gray-100 text-gray-800 border-gray-200",
  "體弱": "bg-pink-100 text-pink-800 border-pink-200"
};

export default function StudentSearchFilter({ onSearch, searchAcrossClasses = false }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTags, setSelectedTags] = useState([]);
  const [selectedClass, setSelectedClass] = useState("all");
  const [allStudents, setAllStudents] = useState([]);
  const [classes, setClasses] = useState([]);
  const [availableTags, setAvailableTags] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [studentsData, classesData] = await Promise.all([
        ClassStudent.filter({ is_active: true }),
        Class.filter({ is_active: true })
      ]);

      // 為學生添加班級資訊
      const studentsWithClass = studentsData.map(student => {
        const studentClass = classesData.find(c => c.id === student.class_id);
        return {
          ...student,
          class_name: studentClass?.class_name || '未知班級'
        };
      });

      setAllStudents(studentsWithClass);
      setClasses(classesData);

      // 收集所有標籤
      const tags = new Set();
      studentsData.forEach(student => {
        if (student.tags && Array.isArray(student.tags)) {
          student.tags.forEach(tag => tags.add(tag));
        }
      });
      setAvailableTags(Array.from(tags));

    } catch (error) {
      console.error("載入學生資料失敗:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchClick = () => {
    let filtered = allStudents;

    // 文字搜尋（姓名、Email、學號）
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(student => 
        student.student_name?.toLowerCase().includes(term) ||
        student.email?.toLowerCase().includes(term) ||
        student.student_id?.toLowerCase().includes(term)
      );
    }

    // 標籤篩選
    if (selectedTags.length > 0) {
      filtered = filtered.filter(student => 
        student.tags && selectedTags.some(tag => student.tags.includes(tag))
      );
    }

    // 班級篩選
    if (selectedClass !== "all") {
      filtered = filtered.filter(student => student.class_id === selectedClass);
    }

    onSearch(filtered);
  };

  const toggleTag = (tag) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const clearFilters = () => {
    setSearchTerm("");
    setSelectedTags([]);
    setSelectedClass("all");
  };

  const getTagColor = (tag) => {
    return TAG_COLORS[tag] || "bg-gray-100 text-gray-800 border-gray-200";
  };

  return (
    <div className="space-y-4">
      {/* 搜尋輸入 */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="搜尋學生姓名、學號或Email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* 班級篩選 */}
      {searchAcrossClasses && (
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <Select value={selectedClass} onValueChange={setSelectedClass}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="選擇班級" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有班級</SelectItem>
              {classes.map(cls => (
                <SelectItem key={cls.id} value={cls.id}>
                  {cls.class_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* 標籤篩選 */}
      {availableTags.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Tag className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">標籤篩選:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {availableTags.map(tag => (
              <Badge
                key={tag}
                variant={selectedTags.includes(tag) ? "default" : "outline"}
                className={`cursor-pointer transition-all ${
                  selectedTags.includes(tag) 
                    ? getTagColor(tag) + " ring-2 ring-offset-1" 
                    : "hover:bg-gray-100"
                }`}
                onClick={() => toggleTag(tag)}
              >
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* 操作按鈕 */}
      <div className="flex justify-end items-center pt-2 border-t gap-2">
        <Button variant="outline" onClick={clearFilters}>
          <X className="w-4 h-4 mr-2" />
          清除篩選
        </Button>
        <Button onClick={handleSearchClick} className="gradient-bg text-white">
            <Search className="w-4 h-4 mr-2"/>
            {loading ? "搜尋中..." : "搜尋"}
        </Button>
      </div>
    </div>
  );
}
