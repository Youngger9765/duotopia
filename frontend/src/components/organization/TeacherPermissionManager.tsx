import { useState, useMemo, memo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import { Search, Save, X, Undo2, Shield, Users } from 'lucide-react';
import {
  PermissionManager,
  TeacherPermissions,
  PERMISSION_TEMPLATES,
  PermissionTemplateName,
  Teacher,
} from '@/lib/permissions';
import { useDebounce } from '@/hooks/useDebounce';

interface TeacherPermissionManagerProps {
  teachers: Teacher[];
  onSavePermissions: (teacherId: number, permissions: TeacherPermissions) => Promise<void>;
  onCancel?: () => void;
}

interface PermissionChanges {
  [teacherId: number]: TeacherPermissions;
}

export const TeacherPermissionManager = memo(function TeacherPermissionManager({
  teachers,
  onSavePermissions,
  onCancel,
}: TeacherPermissionManagerProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<PermissionTemplateName | ''>('');
  const [permissionChanges, setPermissionChanges] = useState<PermissionChanges>({});
  const [saving, setSaving] = useState(false);
  const [selectedTeachers, setSelectedTeachers] = useState<Set<number>>(new Set());

  // Debounce search term for better performance (500ms delay)
  const debouncedSearchTerm = useDebounce(searchTerm, 500);

  // Filter teachers based on debounced search
  const filteredTeachers = useMemo(() => {
    if (!debouncedSearchTerm) return teachers;
    const term = debouncedSearchTerm.toLowerCase();
    return teachers.filter(
      (teacher) =>
        teacher.name.toLowerCase().includes(term) ||
        teacher.email.toLowerCase().includes(term)
    );
  }, [teachers, debouncedSearchTerm]);

  // Get current permissions for a teacher (either modified or original)
  const getTeacherPermissions = (teacherId: number): TeacherPermissions => {
    if (permissionChanges[teacherId]) {
      return permissionChanges[teacherId];
    }
    const teacher = teachers.find((t) => t.id === teacherId);
    return PermissionManager.getAllPermissions(teacher || null);
  };

  // Update a specific permission for a teacher
  const updatePermission = (
    teacherId: number,
    permission: keyof TeacherPermissions,
    value: boolean | number | string[]
  ) => {
    const currentPermissions = getTeacherPermissions(teacherId);
    const newPermissions = { ...currentPermissions, [permission]: value };

    setPermissionChanges({
      ...permissionChanges,
      [teacherId]: newPermissions,
    });
  };

  // Apply template to selected teachers
  const applyTemplate = () => {
    if (!selectedTemplate || selectedTeachers.size === 0) {
      toast.error('Please select a template and at least one teacher');
      return;
    }

    const templatePermissions = PermissionManager.applyTemplate(selectedTemplate);
    const newChanges = { ...permissionChanges };

    selectedTeachers.forEach((teacherId) => {
      newChanges[teacherId] = templatePermissions;
    });

    setPermissionChanges(newChanges);
    toast.success(
      `Applied ${PERMISSION_TEMPLATES[selectedTemplate].name} template to ${selectedTeachers.size} teacher(s)`
    );
  };

  // Toggle teacher selection
  const toggleTeacherSelection = (teacherId: number) => {
    const newSelection = new Set(selectedTeachers);
    if (newSelection.has(teacherId)) {
      newSelection.delete(teacherId);
    } else {
      newSelection.add(teacherId);
    }
    setSelectedTeachers(newSelection);
  };

  // Select all filtered teachers
  const toggleSelectAll = () => {
    if (selectedTeachers.size === filteredTeachers.length) {
      setSelectedTeachers(new Set());
    } else {
      setSelectedTeachers(new Set(filteredTeachers.map((t) => t.id)));
    }
  };

  // Save all changes
  const handleSaveAll = async () => {
    if (Object.keys(permissionChanges).length === 0) {
      toast.info('No changes to save');
      return;
    }

    setSaving(true);
    try {
      const savePromises = Object.entries(permissionChanges).map(([teacherId, permissions]) => {
        if (!PermissionManager.validatePermissions(permissions)) {
          throw new Error(`Invalid permissions for teacher ${teacherId}`);
        }
        return onSavePermissions(parseInt(teacherId), permissions);
      });

      await Promise.all(savePromises);
      toast.success(`Successfully updated permissions for ${savePromises.length} teacher(s)`);
      setPermissionChanges({});
      setSelectedTeachers(new Set());
    } catch (error) {
      toast.error('Failed to save permissions: ' + (error as Error).message);
    } finally {
      setSaving(false);
    }
  };

  // Reset changes
  const handleReset = () => {
    setPermissionChanges({});
    setSelectedTeachers(new Set());
    toast.info('Changes reset');
  };

  // Get role badge
  const getRoleBadge = (teacher: Teacher) => {
    if (PermissionManager.isOrgOwner(teacher)) {
      return (
        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full">
          <Shield className="w-3 h-3 mr-1" />
          Org Owner
        </span>
      );
    }
    if (PermissionManager.isSchoolAdmin(teacher)) {
      return (
        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
          <Shield className="w-3 h-3 mr-1" />
          School Admin
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
        <Users className="w-3 h-3 mr-1" />
        Teacher
      </span>
    );
  };

  const hasChanges = Object.keys(permissionChanges).length > 0;

  return (
    <div className="space-y-4">
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search teachers by name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleReset} disabled={!hasChanges}>
            <Undo2 className="h-4 w-4 mr-2" />
            Reset
          </Button>
          <Button variant="default" size="sm" onClick={handleSaveAll} disabled={!hasChanges || saving}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save All'}
          </Button>
          {onCancel && (
            <Button variant="ghost" size="sm" onClick={onCancel}>
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          )}
        </div>
      </div>

      {/* Bulk Actions */}
      <div className="flex flex-col sm:flex-row gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="flex-1">
          <label className="text-sm font-medium mb-2 block">Apply Template to Selected:</label>
          <div className="flex gap-2">
            <Select value={selectedTemplate} onValueChange={(value) => setSelectedTemplate(value as PermissionTemplateName)}>
              <SelectTrigger className="w-full sm:w-64">
                <SelectValue placeholder="Select template..." />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(PERMISSION_TEMPLATES).map(([key, template]) => (
                  <SelectItem key={key} value={key}>
                    {template.name} - {template.description}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="secondary"
              size="sm"
              onClick={applyTemplate}
              disabled={!selectedTemplate || selectedTeachers.size === 0}
            >
              Apply ({selectedTeachers.size})
            </Button>
          </div>
        </div>
      </div>

      {/* Teachers Table */}
      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedTeachers.size === filteredTeachers.length && filteredTeachers.length > 0}
                    onCheckedChange={toggleSelectAll}
                  />
                </TableHead>
                <TableHead>Teacher</TableHead>
                <TableHead>Role</TableHead>
                <TableHead className="text-center">Create Classrooms</TableHead>
                <TableHead className="text-center">View Others</TableHead>
                <TableHead className="text-center">Manage Students</TableHead>
                <TableHead className="text-center">View All Classes</TableHead>
                <TableHead className="text-center">Edit School</TableHead>
                <TableHead className="text-center">Max Classes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTeachers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-gray-500">
                    No teachers found
                  </TableCell>
                </TableRow>
              ) : (
                filteredTeachers.map((teacher) => {
                  const permissions = getTeacherPermissions(teacher.id);
                  const isSelected = selectedTeachers.has(teacher.id);
                  const hasChange = !!permissionChanges[teacher.id];
                  const isOrgOwner = PermissionManager.isOrgOwner(teacher);

                  return (
                    <TableRow
                      key={teacher.id}
                      className={`${hasChange ? 'bg-yellow-50 dark:bg-yellow-900/10' : ''} ${isSelected ? 'bg-blue-50 dark:bg-blue-900/10' : ''}`}
                    >
                      <TableCell>
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => toggleTeacherSelection(teacher.id)}
                          disabled={isOrgOwner}
                        />
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{teacher.name}</div>
                          <div className="text-sm text-gray-500">{teacher.email}</div>
                        </div>
                      </TableCell>
                      <TableCell>{getRoleBadge(teacher)}</TableCell>
                      <TableCell className="text-center">
                        <Checkbox
                          checked={permissions.can_create_classrooms}
                          onCheckedChange={(checked) =>
                            updatePermission(teacher.id, 'can_create_classrooms', checked === true)
                          }
                          disabled={isOrgOwner}
                        />
                      </TableCell>
                      <TableCell className="text-center">
                        <Checkbox
                          checked={permissions.can_view_other_teachers}
                          onCheckedChange={(checked) =>
                            updatePermission(teacher.id, 'can_view_other_teachers', checked === true)
                          }
                          disabled={isOrgOwner}
                        />
                      </TableCell>
                      <TableCell className="text-center">
                        <Checkbox
                          checked={permissions.can_manage_students}
                          onCheckedChange={(checked) =>
                            updatePermission(teacher.id, 'can_manage_students', checked === true)
                          }
                          disabled={isOrgOwner}
                        />
                      </TableCell>
                      <TableCell className="text-center">
                        <Checkbox
                          checked={permissions.can_view_all_classrooms}
                          onCheckedChange={(checked) =>
                            updatePermission(teacher.id, 'can_view_all_classrooms', checked === true)
                          }
                          disabled={isOrgOwner}
                        />
                      </TableCell>
                      <TableCell className="text-center">
                        <Checkbox
                          checked={permissions.can_edit_school_settings}
                          onCheckedChange={(checked) =>
                            updatePermission(teacher.id, 'can_edit_school_settings', checked === true)
                          }
                          disabled={isOrgOwner}
                        />
                      </TableCell>
                      <TableCell className="text-center">
                        <Input
                          type="number"
                          value={permissions.max_classrooms || 0}
                          onChange={(e) =>
                            updatePermission(teacher.id, 'max_classrooms', parseInt(e.target.value) || 0)
                          }
                          className="w-20 text-center"
                          min={-1}
                          disabled={isOrgOwner}
                        />
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Summary */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Showing {filteredTeachers.length} of {teachers.length} teachers
        {hasChanges && ` • ${Object.keys(permissionChanges).length} pending changes`}
        {selectedTeachers.size > 0 && ` • ${selectedTeachers.size} selected`}
      </div>
    </div>
  );
});
