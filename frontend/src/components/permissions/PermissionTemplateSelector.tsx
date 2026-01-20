import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  PERMISSION_TEMPLATES,
  PermissionTemplateName,
  TeacherPermissions,
} from "@/lib/permissions";
import { Shield, User, Users, Eye, Lock } from "lucide-react";

interface PermissionTemplateSelectorProps {
  selectedTemplate: PermissionTemplateName | "";
  onSelectTemplate: (template: PermissionTemplateName) => void;
  onApplyTemplate?: (permissions: TeacherPermissions) => void;
  showPreview?: boolean;
}

/**
 * Component for selecting and applying permission templates
 */
export function PermissionTemplateSelector({
  selectedTemplate,
  onSelectTemplate,
  onApplyTemplate,
  showPreview = true,
}: PermissionTemplateSelectorProps) {
  const getTemplateIcon = (templateName: PermissionTemplateName) => {
    switch (templateName) {
      case "ORGANIZATION_ADMIN":
        return <Shield className="h-5 w-5 text-purple-600" />;
      case "SCHOOL_ADMIN":
        return <Shield className="h-5 w-5 text-blue-600" />;
      case "SENIOR_TEACHER":
        return <Users className="h-5 w-5 text-green-600" />;
      case "TEACHER":
        return <User className="h-5 w-5 text-orange-600" />;
      case "LIMITED_TEACHER":
        return <Eye className="h-5 w-5 text-gray-600" />;
      case "CUSTOM":
        return <Lock className="h-5 w-5 text-indigo-600" />;
      default:
        return <User className="h-5 w-5 text-gray-600" />;
    }
  };

  const handleTemplateChange = (value: string) => {
    const template = value as PermissionTemplateName;
    onSelectTemplate(template);
    if (onApplyTemplate) {
      const permissions = PERMISSION_TEMPLATES[template].permissions;
      onApplyTemplate(permissions);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="text-sm font-medium mb-2 block">
          Permission Template
        </label>
        <Select value={selectedTemplate} onValueChange={handleTemplateChange}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select a permission template..." />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(PERMISSION_TEMPLATES).map(([key, template]) => (
              <SelectItem key={key} value={key}>
                <div className="flex items-center gap-2">
                  {getTemplateIcon(key as PermissionTemplateName)}
                  <div>
                    <div className="font-medium">{template.name}</div>
                    <div className="text-xs text-gray-500">
                      {template.description}
                    </div>
                  </div>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {showPreview && selectedTemplate && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              {getTemplateIcon(selectedTemplate)}
              {PERMISSION_TEMPLATES[selectedTemplate].name}
            </CardTitle>
            <CardDescription>
              {PERMISSION_TEMPLATES[selectedTemplate].description}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">Permissions:</h4>
              <ul className="space-y-1 text-sm">
                {Object.entries(
                  PERMISSION_TEMPLATES[selectedTemplate].permissions,
                ).map(([key, value]) => {
                  if (key === "allowed_actions") {
                    const actions = value as string[];
                    return (
                      <li key={key} className="flex items-start gap-2">
                        <span className="text-gray-600 min-w-[180px]">
                          Allowed Actions:
                        </span>
                        <span className="font-mono text-xs">
                          {actions.length > 0 ? actions.join(", ") : "None"}
                        </span>
                      </li>
                    );
                  }
                  if (key === "max_classrooms") {
                    return (
                      <li key={key} className="flex items-start gap-2">
                        <span className="text-gray-600 min-w-[180px]">
                          Max Classrooms:
                        </span>
                        <span className="font-medium">
                          {value === -1 ? "Unlimited" : value}
                        </span>
                      </li>
                    );
                  }
                  return (
                    <li key={key} className="flex items-center gap-2">
                      <span
                        className={`h-2 w-2 rounded-full ${value ? "bg-green-500" : "bg-gray-300"}`}
                      />
                      <span className="text-gray-600 min-w-[180px]">
                        {key
                          .replace(/_/g, " ")
                          .replace(/^can /, "")
                          .split(" ")
                          .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                          .join(" ")}
                        :
                      </span>
                      <span
                        className={
                          value ? "text-green-600 font-medium" : "text-gray-400"
                        }
                      >
                        {value ? "Enabled" : "Disabled"}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
