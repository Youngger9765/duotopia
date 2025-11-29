import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import TeacherLayout from "@/components/TeacherLayout";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { Edit2, Trash2, Plus, X, Loader2 } from "lucide-react";

interface Organization {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

interface FormData {
  name: string;
  display_name: string;
  description: string;
  contact_email: string;
  contact_phone: string;
  address: string;
}

export default function OrganizationManagement() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
  const [selectedOrgs, setSelectedOrgs] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();
  const token = useTeacherAuthStore((state) => state.token);

  const [formData, setFormData] = useState<FormData>({
    name: "",
    display_name: "",
    description: "",
    contact_email: "",
    contact_phone: "",
    address: "",
  });

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const fetchOrganizations = async () => {
    try {
      console.log(
        "🔍 Fetching organizations with token:",
        token?.substring(0, 20) + "...",
      );

      const response = await fetch("/api/organizations", {
        headers: { Authorization: `Bearer ${token}` },
      });

      console.log("📡 API Response status:", response.status);

      if (response.ok) {
        const data = await response.json();
        console.log("✅ Organizations data:", data);
        setOrganizations(data);
      } else {
        const error = await response.text();
        console.error("❌ API Error:", response.status, error);
        toast.error("Failed to load organizations");
      }
    } catch (error) {
      console.error("❌ Failed to fetch organizations:", error);
      toast.error("Network error loading organizations");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      display_name: "",
      description: "",
      contact_email: "",
      contact_phone: "",
      address: "",
    });
  };

  const handleEdit = (org: Organization) => {
    setEditingOrg(org);
    setFormData({
      name: org.name,
      display_name: org.display_name || "",
      description: org.description || "",
      contact_email: org.contact_email || "",
      contact_phone: "",
      address: "",
    });
    setShowEditForm(true);
  };

  const handleDelete = async (orgId: string) => {
    if (!confirm("Are you sure you want to delete this organization? This action cannot be undone.")) {
      return;
    }

    setDeleting(true);
    try {
      const response = await fetch(`/api/organizations/${orgId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        toast.success("Organization deleted successfully");
        setOrganizations(organizations.filter((org) => org.id !== orgId));
      } else {
        const error = await response.text();
        toast.error(`Failed to delete: ${error}`);
      }
    } catch (error) {
      console.error("Delete failed:", error);
      toast.error("Error deleting organization");
    } finally {
      setDeleting(false);
    }
  };

  const handleBatchDelete = async () => {
    if (selectedOrgs.size === 0) {
      toast.info("Please select organizations to delete");
      return;
    }

    if (!confirm(`Delete ${selectedOrgs.size} selected organization(s)? This action cannot be undone.`)) {
      return;
    }

    setDeleting(true);
    try {
      const deletePromises = Array.from(selectedOrgs).map((orgId) =>
        fetch(`/api/organizations/${orgId}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        })
      );

      await Promise.all(deletePromises);
      toast.success(`Deleted ${selectedOrgs.size} organization(s)`);
      setOrganizations(organizations.filter((org) => !selectedOrgs.has(org.id)));
      setSelectedOrgs(new Set());
    } catch (error) {
      console.error("Batch delete failed:", error);
      toast.error("Error deleting organizations");
    } finally {
      setDeleting(false);
    }
  };

  const toggleOrgSelection = (orgId: string) => {
    const newSelection = new Set(selectedOrgs);
    if (newSelection.has(orgId)) {
      newSelection.delete(orgId);
    } else {
      newSelection.add(orgId);
    }
    setSelectedOrgs(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedOrgs.size === organizations.length) {
      setSelectedOrgs(new Set());
    } else {
      setSelectedOrgs(new Set(organizations.map((org) => org.id)));
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await fetch("/api/organizations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("Organization created successfully");
        setShowCreateForm(false);
        resetForm();
        fetchOrganizations();
      } else {
        const error = await response.text();
        toast.error(`Failed to create: ${error}`);
      }
    } catch (error) {
      console.error("Create failed:", error);
      toast.error("Error creating organization");
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingOrg) return;

    setSaving(true);
    try {
      const response = await fetch(`/api/organizations/${editingOrg.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success("Organization updated successfully");
        setShowEditForm(false);
        setEditingOrg(null);
        resetForm();
        fetchOrganizations();
      } else {
        const error = await response.text();
        toast.error(`Failed to update: ${error}`);
      }
    } catch (error) {
      console.error("Update failed:", error);
      toast.error("Error updating organization");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <TeacherLayout>
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2">Loading organizations...</span>
        </div>
      </TeacherLayout>
    );
  }

  const FormModal = ({ isEdit = false, onSubmit, onClose }: { isEdit?: boolean; onSubmit: (e: React.FormEvent) => void; onClose: () => void }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">{isEdit ? "編輯機構" : "創建新機構"}</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block mb-2 text-sm font-medium">機構名稱 *</label>
            <Input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Enter organization name"
            />
          </div>
          <div>
            <label className="block mb-2 text-sm font-medium">顯示名稱</label>
            <Input
              type="text"
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              placeholder="Display name (optional)"
            />
          </div>
          <div>
            <label className="block mb-2 text-sm font-medium">描述</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full border rounded px-3 py-2 dark:bg-gray-700 dark:border-gray-600"
              rows={3}
              placeholder="Organization description"
            />
          </div>
          <div>
            <label className="block mb-2 text-sm font-medium">聯絡電郵</label>
            <Input
              type="email"
              value={formData.contact_email}
              onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
              placeholder="contact@example.com"
            />
          </div>
          <div>
            <label className="block mb-2 text-sm font-medium">聯絡電話</label>
            <Input
              type="tel"
              value={formData.contact_phone}
              onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
              placeholder="+1234567890"
            />
          </div>
          <div className="flex gap-2 justify-end pt-4">
            <Button type="button" variant="outline" onClick={onClose} disabled={saving}>
              取消
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {isEdit ? "更新中..." : "創建中..."}
                </>
              ) : (
                isEdit ? "更新" : "創建"
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );

  return (
    <TeacherLayout>
      <div className="p-8 max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <h1 className="text-3xl font-bold">機構管理</h1>
          <div className="flex gap-2">
            {selectedOrgs.size > 0 && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleBatchDelete}
                disabled={deleting}
              >
                {deleting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    刪除中...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4 mr-2" />
                    刪除選中 ({selectedOrgs.size})
                  </>
                )}
              </Button>
            )}
            <Button onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              新增機構
            </Button>
          </div>
        </div>

        {/* Batch Selection Bar */}
        {organizations.length > 0 && (
          <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Checkbox
                checked={selectedOrgs.size === organizations.length && organizations.length > 0}
                onCheckedChange={toggleSelectAll}
              />
              <span className="text-sm font-medium">Select All</span>
            </div>
            {selectedOrgs.size > 0 && (
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {selectedOrgs.size} of {organizations.length} selected
              </span>
            )}
          </div>
        )}

        {/* Create Modal */}
        {showCreateForm && (
          <FormModal
            isEdit={false}
            onSubmit={handleCreate}
            onClose={() => {
              setShowCreateForm(false);
              resetForm();
            }}
          />
        )}

        {/* Edit Modal */}
        {showEditForm && editingOrg && (
          <FormModal
            isEdit={true}
            onSubmit={handleUpdate}
            onClose={() => {
              setShowEditForm(false);
              setEditingOrg(null);
              resetForm();
            }}
          />
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {organizations.map((org) => {
            const isSelected = selectedOrgs.has(org.id);
            return (
              <div
                key={org.id}
                className={`border rounded-lg p-6 hover:shadow-lg transition-all ${
                  isSelected ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900/10' : ''
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => toggleOrgSelection(org.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <h3
                      className="text-xl font-semibold cursor-pointer hover:text-blue-600"
                      onClick={() => navigate(`/teacher/organizations/${org.id}`)}
                    >
                      {org.display_name || org.name}
                    </h3>
                  </div>
                </div>

                {org.description && (
                  <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm line-clamp-2">
                    {org.description}
                  </p>
                )}

                <div className="text-sm text-gray-500 dark:text-gray-400 space-y-1 mb-4">
                  {org.contact_email && (
                    <div className="flex items-center gap-1">
                      📧 <span className="truncate">{org.contact_email}</span>
                    </div>
                  )}
                  <div>
                    創建時間: {new Date(org.created_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="flex gap-2 pt-4 border-t dark:border-gray-700">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/teacher/organizations/${org.id}`);
                    }}
                  >
                    查看詳情
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEdit(org);
                    }}
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(org.id);
                    }}
                    disabled={deleting}
                  >
                    <Trash2 className="h-4 w-4 text-red-600" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>

        {organizations.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <p>尚無機構，點擊上方按鈕創建第一個機構</p>
          </div>
        )}
      </div>
    </TeacherLayout>
  );
}
