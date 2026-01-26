/**
 * PersonalTab - Personal workspace content
 *
 * This is a passthrough component that renders the existing
 * teacher sidebar menu items (my classes, my students, my materials)
 */

import React from 'react';

export const PersonalTab: React.FC = () => {
  return (
    <div className="space-y-1">
      {/*
        This component will be integrated with the existing sidebar menu.
        For now, it's a placeholder that will be populated when
        we integrate WorkspaceSwitcher into the actual Sidebar component.

        Expected menu items:
        - 我的班級 (My Classes)
        - 我的學生 (My Students)
        - 我的教材 (My Materials)
      */}
      <p className="text-sm text-slate-500 dark:text-slate-400 px-3 py-2">
        個人工作區選單（將整合現有側邊欄）
      </p>
    </div>
  );
};

export default PersonalTab;
