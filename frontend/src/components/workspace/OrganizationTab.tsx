/**
 * OrganizationTab - Organization workspace content
 *
 * Two-phase navigation:
 * Phase 1: Show organization + school list for selection
 * Phase 2: After selection, show school switcher + functional menu
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import SchoolList from './SchoolList';
import SchoolSwitcher from './SchoolSwitcher';
import PermissionBanner from './PermissionBanner';

export const OrganizationTab: React.FC = () => {
  const { t } = useTranslation();
  const { selectedSchool, error } = useWorkspace();

  if (error) {
    return (
      <div className="px-3 py-4 rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
        <p className="text-sm text-red-800 dark:text-red-200">
          {t('workspace.organization.error')}: {error}
        </p>
      </div>
    );
  }

  // Phase 1: No school selected, show org + school list
  if (!selectedSchool) {
    return <SchoolList />;
  }

  // Phase 2: School selected, show switcher + banner
  return (
    <div className="space-y-4">
      {/* School Switcher */}
      <SchoolSwitcher />

      {/* Permission Banner */}
      <PermissionBanner />
    </div>
  );
};

export default OrganizationTab;
