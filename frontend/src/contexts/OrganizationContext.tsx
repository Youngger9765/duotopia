import { createContext, useContext, useState, ReactNode, useMemo } from "react";

interface Organization {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

interface SchoolData {
  id: string;
  organization_id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

type NodeType = "organization" | "school";

interface SelectedNode {
  type: NodeType;
  id: string;
  data: Organization | SchoolData;
}

interface OrganizationContextType {
  selectedNode: SelectedNode | null;
  setSelectedNode: React.Dispatch<React.SetStateAction<SelectedNode | null>>;
  organizations: Organization[];
  setOrganizations: React.Dispatch<React.SetStateAction<Organization[]>>;
  schools: Record<string, SchoolData[]>;
  setSchools: React.Dispatch<
    React.SetStateAction<Record<string, SchoolData[]>>
  >;
  expandedOrgs: string[];
  setExpandedOrgs: React.Dispatch<React.SetStateAction<string[]>>;
  isFetchingOrgs: boolean;
  setIsFetchingOrgs: React.Dispatch<React.SetStateAction<boolean>>;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(
  undefined,
);

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [schools, setSchools] = useState<Record<string, SchoolData[]>>({});
  const [expandedOrgs, setExpandedOrgs] = useState<string[]>([]);
  const [isFetchingOrgs, setIsFetchingOrgs] = useState(false);

  // Memoize context value to prevent unnecessary re-renders
  const contextValue = useMemo(
    () => ({
      selectedNode,
      setSelectedNode,
      organizations,
      setOrganizations,
      schools,
      setSchools,
      expandedOrgs,
      setExpandedOrgs,
      isFetchingOrgs,
      setIsFetchingOrgs,
    }),
    [selectedNode, organizations, schools, expandedOrgs, isFetchingOrgs],
  );

  return (
    <OrganizationContext.Provider value={contextValue}>
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization() {
  const context = useContext(OrganizationContext);
  if (context === undefined) {
    throw new Error(
      "useOrganization must be used within an OrganizationProvider",
    );
  }
  return context;
}
