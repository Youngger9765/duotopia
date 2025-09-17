import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Database,
  RefreshCw,
  Users,
  GraduationCap,
  School,
  BookOpen,
  FileText,
  ClipboardCheck,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';

interface DatabaseStats {
  entities: {
    teacher: number;
    student: number;
    classroom: number;
    classroom_student: number;
    program: number;
    lesson: number;
    content: number;
    assignment: number;
    student_assignment: number;
  };
  total_records: number;
}

interface EntityData {
  data: Record<string, unknown>[];
  total: number;
  pagination: {
    limit: number;
    offset: number;
    has_more: boolean;
  };
}

const entityConfig = [
  { key: 'teacher', name: '教師', icon: Users, color: 'bg-blue-500' },
  { key: 'student', name: '學生', icon: GraduationCap, color: 'bg-green-500' },
  { key: 'classroom', name: '班級', icon: School, color: 'bg-purple-500' },
  { key: 'classroom_student', name: '班級學生', icon: Users, color: 'bg-orange-500' },
  { key: 'program', name: '課程計畫', icon: BookOpen, color: 'bg-indigo-500' },
  { key: 'lesson', name: '課程單元', icon: FileText, color: 'bg-pink-500' },
  { key: 'content', name: '學習內容', icon: FileText, color: 'bg-teal-500' },
  { key: 'assignment', name: '作業', icon: ClipboardCheck, color: 'bg-red-500' },
  { key: 'student_assignment', name: '學生作業', icon: ClipboardCheck, color: 'bg-yellow-500' },
];

export default function DatabaseAdminPage() {
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
  const [entityData, setEntityData] = useState<EntityData | null>(null);
  const [loadingEntity, setLoadingEntity] = useState(false);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/admin/database/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        toast.error('無法載入統計資料');
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
      toast.error('載入統計資料失敗');
    } finally {
      setLoading(false);
    }
  };

  const fetchEntityData = async (entityType: string) => {
    setLoadingEntity(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/admin/database/entity/${entityType}`);
      if (response.ok) {
        const data = await response.json();
        setEntityData(data);
        setSelectedEntity(entityType);
      } else {
        toast.error(`無法載入 ${entityType} 資料`);
      }
    } catch (error) {
      console.error('Error fetching entity data:', error);
      toast.error('載入資料失敗');
    } finally {
      setLoadingEntity(false);
    }
  };

  const handleSeedDatabase = async () => {
    if (!confirm('確定要重建整個資料庫嗎？這會清除所有現有資料！')) {
      return;
    }

    setSeeding(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/admin/database/rebuild`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ seed: true })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        toast.success('資料庫重建成功！');
        fetchStats(); // 重新載入統計
        if (selectedEntity) {
          fetchEntityData(selectedEntity); // 重新載入選中的資料
        }
      } else {
        // 處理 HTTP 錯誤或業務邏輯錯誤
        const errorMessage = result.detail || result.message || '未知錯誤';
        toast.error(`重建失敗: ${errorMessage}`);
        console.error('Seed error:', result);
      }
    } catch (error) {
      console.error('Error seeding database:', error);
      toast.error('重建資料庫失敗');
    } finally {
      setSeeding(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">載入中...</span>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar - Entity List */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3 mb-4">
            <Database className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-xl font-bold">資料庫管理</h1>
              <p className="text-sm text-gray-600">
                總記錄數: {stats?.total_records || 0}
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={fetchStats}
              variant="outline"
              size="sm"
              disabled={loading}
              className="flex-1"
            >
              <RefreshCw className={`h-3 w-3 mr-2 ${loading ? 'animate-spin' : ''}`} />
              重新整理
            </Button>

            <Button
              onClick={handleSeedDatabase}
              disabled={seeding}
              size="sm"
              className="flex-1 bg-green-600 hover:bg-green-700"
            >
              {seeding ? (
                <>
                  <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                  重建中
                </>
              ) : (
                <>
                  <RefreshCw className="h-3 w-3 mr-2" />
                  重建資料庫
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Entity List */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-3">
            {entityConfig.map(({ key, name, icon: Icon, color }) => {
              const count = stats?.entities[key as keyof typeof stats.entities] || 0;
              const isSelected = selectedEntity === key;

              return (
                <div
                  key={key}
                  className={`p-4 rounded-lg border transition-all cursor-pointer ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 shadow-md'
                      : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                  }`}
                  onClick={() => fetchEntityData(key)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${color} text-white`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div>
                        <h3 className="font-medium text-sm">{name}</h3>
                        <p className="text-xs text-gray-500">{key}</p>
                      </div>
                    </div>
                    <Badge variant={isSelected ? "default" : "secondary"} className="text-sm font-bold">
                      {count}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right Panel - Entity Details */}
      <div className="flex-1 flex flex-col">
        {selectedEntity && entityData ? (
          <>
            {/* Detail Header */}
            <div className="p-6 bg-white border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {(() => {
                    const config = entityConfig.find(e => e.key === selectedEntity);
                    const Icon = config?.icon || Database;
                    return (
                      <div className={`p-3 rounded-lg ${config?.color || 'bg-gray-500'} text-white`}>
                        <Icon className="h-6 w-6" />
                      </div>
                    );
                  })()}
                  <div>
                    <h2 className="text-xl font-bold">
                      {entityConfig.find(e => e.key === selectedEntity)?.name || selectedEntity}
                    </h2>
                    <p className="text-gray-600">
                      共 {entityData.total} 筆記錄
                    </p>
                  </div>
                </div>
                <Button
                  onClick={() => setSelectedEntity(null)}
                  variant="outline"
                  size="sm"
                >
                  關閉
                </Button>
              </div>
            </div>

            {/* Detail Content */}
            <div className="flex-1 overflow-hidden">
              {loadingEntity ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="h-8 w-8 animate-spin mr-3" />
                  <span className="text-lg">載入中...</span>
                </div>
              ) : (
                <div className="h-full overflow-auto p-6">
                  {entityData.data.length > 0 ? (
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead className="bg-gray-50">
                            <tr>
                              {Object.keys(entityData.data[0]).map(key => (
                                <th key={key} className="text-left p-3 font-medium text-gray-900 border-b">
                                  {key}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-200">
                            {entityData.data.map((item, index) => (
                              <tr key={index} className="hover:bg-gray-50">
                                {Object.values(item).map((value, i) => (
                                  <td key={i} className="p-3 text-sm">
                                    <div className="max-w-xs truncate" title={String(value)}>
                                      {typeof value === 'string' && value.length > 30
                                        ? `${value.substring(0, 30)}...`
                                        : String(value)}
                                    </div>
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <Database className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">暫無資料</h3>
                        <p className="text-gray-500">此 Entity 目前沒有任何記錄</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        ) : (
          /* Welcome Screen */
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Database className="h-24 w-24 text-gray-300 mx-auto mb-6" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">選擇 Entity 查看詳細資料</h2>
              <p className="text-gray-500 mb-6">點擊左側任一 Entity 來查看其完整資料</p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left max-w-md mx-auto">
                <h3 className="font-medium text-blue-900 mb-2">💡 功能提示</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• 點擊左側卡片查看資料</li>
                  <li>• 使用「重建資料庫」重新產生所有資料</li>
                  <li>• 「重新整理」可更新統計數字</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
