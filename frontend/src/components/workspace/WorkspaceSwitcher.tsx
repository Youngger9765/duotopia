/**
 * WorkspaceSwitcher - Main component for teacher workspace switching
 *
 * Provides Tab interface to switch between:
 * - Personal mode (my classes, my students, my materials)
 * - Organization mode (organization schools and materials)
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import PersonalTab from './PersonalTab';
import OrganizationTab from './OrganizationTab';

export const WorkspaceSwitcher: React.FC = () => {
  const { t } = useTranslation();
  const { mode, setMode, organizations } = useWorkspace();

  // If teacher has no organizations, don't show tabs - just show personal mode
  if (organizations.length === 0) {
    return (
      <div className="mb-4 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
        <div className="text-sm text-slate-600 dark:text-slate-400">
          {t('workspace.personalModeOnly')}
        </div>
      </div>
    );
  }

  // If has organizations, show full tabs UI
  return (
    <div className="mb-4">
      <Tabs value={mode} onValueChange={(value) => setMode(value as 'personal' | 'organization')}>
        <TabsList className="grid w-full grid-cols-2 h-12">
          <TabsTrigger
            value="personal"
            className="data-[state=active]:bg-white data-[state=active]:text-blue-600 data-[state=active]:border data-[state=active]:border-slate-200 data-[state=active]:shadow-sm dark:data-[state=active]:bg-slate-700 dark:data-[state=active]:text-blue-400 dark:data-[state=active]:border-slate-600 transition-all duration-200"
          >
            {t('workspace.tabs.personal')}
          </TabsTrigger>
          <TabsTrigger
            value="organization"
            className="data-[state=active]:bg-white data-[state=active]:text-blue-600 data-[state=active]:border data-[state=active]:border-slate-200 data-[state=active]:shadow-sm dark:data-[state=active]:bg-slate-700 dark:data-[state=active]:text-blue-400 dark:data-[state=active]:border-slate-600 transition-all duration-200"
          >
            {t('workspace.tabs.organization')}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="personal" className="mt-4">
          <PersonalTab />
        </TabsContent>

        <TabsContent value="organization" className="mt-4">
          <OrganizationTab />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WorkspaceSwitcher;
