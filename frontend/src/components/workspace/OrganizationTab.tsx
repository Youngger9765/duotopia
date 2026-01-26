/**
 * OrganizationTab - Organization workspace content
 *
 * Two-phase navigation:
 * Phase 1: Show organization + school list for selection
 * Phase 2: After selection, show school switcher + functional menu
 */

import React from 'react';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import SchoolList from './SchoolList';
import SchoolSwitcher from './SchoolSwitcher';
import PermissionBanner from './PermissionBanner';

export const OrganizationTab: React.FC = () => {
  const { selectedSchool, error } = useWorkspace();

  if (error) {
    return (
      <div className="px-3 py-4 rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
        <p className="text-sm text-red-800 dark:text-red-200">
          載入機構資料時發生錯誤：{error}
        </p>
      </div>
    );
  }

  // Phase 1: No school selected, show org + school list
  if (!selectedSchool) {
    return <SchoolList />;
  }

  // Phase 2: School selected, show switcher + menu
  return (
    <div className="space-y-4">
      {/* School Switcher */}
      <SchoolSwitcher />

      {/* Permission Banner */}
      <PermissionBanner />

      {/* Functional Menu (will be integrated with existing sidebar items) */}
      <div className="space-y-1">
        <p className="text-sm text-slate-500 dark:text-slate-400 px-3 py-2">
          功能選單（將整合班級、教材、作業等功能）
        </p>
      </div>
    </div>
  );
};

export default OrganizationTab;
