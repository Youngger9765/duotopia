/**
 * PersonalTab - Personal workspace content
 *
 * This is a passthrough component that renders the existing
 * teacher sidebar menu items (my classes, my students, my materials)
 */

import React from "react";
import { useTranslation } from "react-i18next";

export const PersonalTab: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="px-3 py-2">
      <p className="text-xs text-slate-500 dark:text-slate-400">
        {t("workspace.personal.description")}
      </p>
    </div>
  );
};

export default PersonalTab;
