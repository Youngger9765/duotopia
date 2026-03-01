import {
  createContext,
  useContext,
  useState,
  ReactNode,
  useMemo,
  useCallback,
} from "react";
import { API_URL } from "@/config/api";

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
  // Refresh functions for syncing state after CRUD operations
  refreshOrganizations: (token: string) => Promise<void>;
  refreshSchools: (token: string, orgId: string) => Promise<void>;
}

export const OrganizationContext = createContext<
  OrganizationContextType | undefined
>(undefined);

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [schools, setSchools] = useState<Record<string, SchoolData[]>>({});
  const [expandedOrgs, setExpandedOrgs] = useState<string[]>([]);
  const [isFetchingOrgs, setIsFetchingOrgs] = useState(false);

  // Refresh organizations from API - call after CRUD operations
  const refreshOrganizations = useCallback(async (token: string) => {
    if (!token) {
      console.warn("refreshOrganizations called without token");
      return;
    }
    try {
      setIsFetchingOrgs(true);
      const response = await fetch(`${API_URL}/api/organizations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setOrganizations(data);
      } else {
        console.error("Failed to refresh organizations:", response.status);
      }
    } catch (error) {
      console.error("Failed to refresh organizations:", error);
    } finally {
      setIsFetchingOrgs(false);
    }
  }, []);

  // Refresh schools for a specific org - call after CRUD operations
  const refreshSchools = useCallback(async (token: string, orgId: string) => {
    if (!token || !orgId) {
      console.warn("refreshSchools called without token or orgId");
      return;
    }
    try {
      const response = await fetch(
        `${API_URL}/api/schools?organization_id=${orgId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (response.ok) {
        const data = await response.json();
        setSchools((prev) => ({ ...prev, [orgId]: data }));
      } else {
        console.error("Failed to refresh schools:", response.status);
      }
    } catch (error) {
      console.error("Failed to refresh schools:", error);
    }
  }, []);

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
      refreshOrganizations,
      refreshSchools,
    }),
    [
      selectedNode,
      organizations,
      schools,
      expandedOrgs,
      isFetchingOrgs,
      refreshOrganizations,
      refreshSchools,
    ],
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
