# Teacher Workspace Switcher Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Sidebar Tab switcher that lets teachers clearly separate personal workspace (full permissions) from organization/school workspace (restricted permissions)

**Architecture:**
- Add Tab component to TeacherLayout Sidebar (Personal/Organization modes)
- Create WorkspaceContext for state management (current mode, selected org/school)
- Build two-phase organization navigation (school list → school switcher + menu)
- Visual permission indicators (banner + read-only badges)

**Tech Stack:**
- React 18 + TypeScript
- shadcn/ui (Tabs, Select, Alert, ScrollArea)
- Zustand (workspace state persistence)
- React Router (navigation)
- Tailwind CSS (styling)

**Design Reference:** `docs/plans/2026-01-26-teacher-workspace-switcher-design.md`

---

## Pre-Implementation Checklist

Before starting, verify:
- [ ] Read design spec: `docs/plans/2026-01-26-teacher-workspace-switcher-design.md`
- [ ] Current branch: `feat/issue-112-org-hierarchy`
- [ ] Frontend dev server running: `cd frontend && npm run dev`
- [ ] Backend API running: `cd backend && uvicorn app.main:app --reload --port 8000`

---

## Phase 1: Backend API - Teacher Organizations Endpoint

### Task 1.1: Create GET /api/teachers/organizations endpoint

**Files:**
- Create: `backend/routers/teachers/teacher_organizations.py`
- Modify: `backend/routers/teachers/__init__.py`
- Test: `backend/tests/test_teacher_organizations.py`

**Step 1: Write the failing test**

Create `backend/tests/test_teacher_organizations.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models import Teacher, Organization, School, TeacherOrganization


class TestGetTeacherOrganizations:
    """Test GET /api/teachers/organizations endpoint"""

    def test_get_organizations_success(
        self,
        test_client: TestClient,
        test_db: Session,
        auth_headers: dict,
        test_teacher: Teacher,
    ):
        """Should return list of organizations with schools for authenticated teacher"""
        # Setup: Create org + schools + teacher membership
        org = Organization(name="Test Org", code="TEST001")
        test_db.add(org)
        test_db.flush()

        school1 = School(name="School A", organization_id=org.id)
        school2 = School(name="School B", organization_id=org.id)
        test_db.add_all([school1, school2])
        test_db.flush()

        teacher_org = TeacherOrganization(
            teacher_id=test_teacher.id,
            organization_id=org.id,
            role="org_admin",
            is_active=True,
        )
        test_db.add(teacher_org)
        test_db.commit()

        # Execute
        response = test_client.get(
            "/api/teachers/organizations",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "organizations" in data
        assert len(data["organizations"]) == 1

        org_data = data["organizations"][0]
        assert org_data["id"] == str(org.id)
        assert org_data["name"] == "Test Org"
        assert org_data["role"] == "org_admin"
        assert len(org_data["schools"]) == 2
        assert org_data["schools"][0]["name"] == "School A"

    def test_get_organizations_no_memberships(
        self,
        test_client: TestClient,
        auth_headers: dict,
    ):
        """Should return empty list when teacher not in any organization"""
        response = test_client.get(
            "/api/teachers/organizations",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["organizations"] == []

    def test_get_organizations_unauthorized(self, test_client: TestClient):
        """Should return 401 without auth"""
        response = test_client.get("/api/teachers/organizations")
        assert response.status_code == 401
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_teacher_organizations.py::TestGetTeacherOrganizations -v
```

Expected: FAIL with "404 Not Found" (endpoint doesn't exist yet)

**Step 3: Write minimal implementation**

Create `backend/routers/teachers/teacher_organizations.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models import Teacher, Organization, School, TeacherOrganization, TeacherSchool
from app.routers.auth import get_current_teacher

router = APIRouter(prefix="/teachers", tags=["teachers"])


class SchoolResponse(BaseModel):
    id: str
    name: str
    role: str | None = None

    class Config:
        from_attributes = True


class OrganizationResponse(BaseModel):
    id: str
    name: str
    role: str
    schools: List[SchoolResponse]

    class Config:
        from_attributes = True


class TeacherOrganizationsResponse(BaseModel):
    organizations: List[OrganizationResponse]


@router.get("/organizations", response_model=TeacherOrganizationsResponse)
def get_teacher_organizations(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Get all organizations and schools that the teacher is a member of"""

    # Query teacher's organization memberships
    org_memberships = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == current_teacher.id,
            TeacherOrganization.is_active.is_(True),
        )
        .all()
    )

    organizations = []

    for membership in org_memberships:
        org = (
            db.query(Organization)
            .filter(Organization.id == membership.organization_id)
            .first()
        )

        if not org:
            continue

        # Get all schools in this organization
        schools = (
            db.query(School)
            .filter(School.organization_id == org.id, School.is_active.is_(True))
            .all()
        )

        # Check teacher's role in each school (if any)
        school_responses = []
        for school in schools:
            teacher_school = (
                db.query(TeacherSchool)
                .filter(
                    TeacherSchool.teacher_id == current_teacher.id,
                    TeacherSchool.school_id == school.id,
                    TeacherSchool.is_active.is_(True),
                )
                .first()
            )

            # Extract role from JSONB array if exists
            school_role = None
            if teacher_school and teacher_school.roles:
                roles = teacher_school.roles
                if isinstance(roles, list) and len(roles) > 0:
                    school_role = roles[0]  # Take first role

            school_responses.append(
                SchoolResponse(
                    id=str(school.id),
                    name=school.name,
                    role=school_role,
                )
            )

        organizations.append(
            OrganizationResponse(
                id=str(org.id),
                name=org.name,
                role=membership.role,
                schools=school_responses,
            )
        )

    return TeacherOrganizationsResponse(organizations=organizations)
```

**Step 4: Register router**

Modify `backend/routers/teachers/__init__.py`:

```python
from fastapi import APIRouter
from .classroom_ops import router as classroom_router
from .student_ops import router as student_router
from .content_ops import router as content_router
from .teacher_organizations import router as teacher_orgs_router  # Add this

router = APIRouter()
router.include_router(classroom_router)
router.include_router(student_router)
router.include_router(content_ops)
router.include_router(teacher_orgs_router)  # Add this
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_teacher_organizations.py::TestGetTeacherOrganizations -v
```

Expected: PASS (3/3 tests green)

**Step 6: Test manually with curl**

```bash
# Get teacher token first
TOKEN=$(curl -X POST http://localhost:8000/api/teachers/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@duotopia.com","password":"demo123"}' \
  | jq -r '.access_token')

# Call the endpoint
curl -X GET http://localhost:8000/api/teachers/organizations \
  -H "Authorization: Bearer $TOKEN" | jq
```

Expected: JSON with organizations array

**Step 7: Commit**

```bash
git add backend/routers/teachers/teacher_organizations.py \
        backend/routers/teachers/__init__.py \
        backend/tests/test_teacher_organizations.py
git commit -m "feat(api): add GET /api/teachers/organizations endpoint

- Returns list of organizations with nested schools
- Includes teacher's role in each org and school
- Filters for active memberships only
- Tests: organization memberships, empty list, unauthorized

Resolves teacher workspace switcher backend requirement"
```

---

## Phase 2: Frontend State Management

### Task 2.1: Create Workspace Context

**Files:**
- Create: `frontend/src/contexts/WorkspaceContext.tsx`
- Create: `frontend/src/hooks/useWorkspace.ts`
- Test: Manual (will add tests in Phase 5)

**Step 1: Create WorkspaceContext**

Create `frontend/src/contexts/WorkspaceContext.tsx`:

```typescript
import React, { createContext, useState, useEffect, ReactNode } from "react";

export type WorkspaceMode = "personal" | "organization";

export interface School {
  id: string;
  name: string;
  role?: string | null;
}

export interface Organization {
  id: string;
  name: string;
  role: string;
  schools: School[];
}

export interface WorkspaceContextType {
  mode: WorkspaceMode;
  setMode: (mode: WorkspaceMode) => void;

  selectedOrganization: Organization | null;
  setSelectedOrganization: (org: Organization | null) => void;

  selectedSchool: School | null;
  setSelectedSchool: (school: School | null) => void;

  organizations: Organization[];
  setOrganizations: (orgs: Organization[]) => void;

  loading: boolean;
  setLoading: (loading: boolean) => void;
}

export const WorkspaceContext = createContext<WorkspaceContextType | undefined>(
  undefined
);

interface WorkspaceProviderProps {
  children: ReactNode;
}

export function WorkspaceProvider({ children }: WorkspaceProviderProps) {
  // Load mode from localStorage, default to personal
  const [mode, setModeState] = useState<WorkspaceMode>(() => {
    const saved = localStorage.getItem("workspace:mode");
    return (saved as WorkspaceMode) || "personal";
  });

  const [selectedOrganization, setSelectedOrganizationState] =
    useState<Organization | null>(() => {
      const saved = localStorage.getItem("workspace:organization");
      return saved ? JSON.parse(saved) : null;
    });

  const [selectedSchool, setSelectedSchoolState] = useState<School | null>(
    () => {
      const saved = localStorage.getItem("workspace:school");
      return saved ? JSON.parse(saved) : null;
    }
  );

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(false);

  // Persist mode to localStorage
  const setMode = (newMode: WorkspaceMode) => {
    setModeState(newMode);
    localStorage.setItem("workspace:mode", newMode);

    // Clear organization/school when switching to personal
    if (newMode === "personal") {
      setSelectedOrganizationState(null);
      setSelectedSchoolState(null);
      localStorage.removeItem("workspace:organization");
      localStorage.removeItem("workspace:school");
    }
  };

  // Persist organization to localStorage
  const setSelectedOrganization = (org: Organization | null) => {
    setSelectedOrganizationState(org);
    if (org) {
      localStorage.setItem("workspace:organization", JSON.stringify(org));
    } else {
      localStorage.removeItem("workspace:organization");
    }

    // Clear school selection when org changes
    setSelectedSchoolState(null);
    localStorage.removeItem("workspace:school");
  };

  // Persist school to localStorage
  const setSelectedSchool = (school: School | null) => {
    setSelectedSchoolState(school);
    if (school) {
      localStorage.setItem("workspace:school", JSON.stringify(school));
    } else {
      localStorage.removeItem("workspace:school");
    }
  };

  const value: WorkspaceContextType = {
    mode,
    setMode,
    selectedOrganization,
    setSelectedOrganization,
    selectedSchool,
    setSelectedSchool,
    organizations,
    setOrganizations,
    loading,
    setLoading,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}
```

**Step 2: Create useWorkspace hook**

Create `frontend/src/hooks/useWorkspace.ts`:

```typescript
import { useContext } from "react";
import { WorkspaceContext, WorkspaceContextType } from "@/contexts/WorkspaceContext";

export function useWorkspace(): WorkspaceContextType {
  const context = useContext(WorkspaceContext);

  if (context === undefined) {
    throw new Error("useWorkspace must be used within WorkspaceProvider");
  }

  return context;
}
```

**Step 3: Wrap TeacherLayout with provider**

Modify `frontend/src/App.tsx` (find TeacherLayout routes and wrap):

```typescript
import { WorkspaceProvider } from "@/contexts/WorkspaceContext";

// In your router configuration, wrap teacher routes:
<Route path="/teacher/*" element={
  <WorkspaceProvider>
    <TeacherLayout>
      <Outlet />
    </TeacherLayout>
  </WorkspaceProvider>
} />
```

**Step 4: Test in browser console**

```bash
cd frontend && npm run dev
```

Open browser console on teacher page:

```javascript
// Should have workspace mode in localStorage
localStorage.getItem('workspace:mode')  // "personal"

// Context should be available (check React DevTools)
// Look for WorkspaceProvider in component tree
```

**Step 5: Commit**

```bash
git add frontend/src/contexts/WorkspaceContext.tsx \
        frontend/src/hooks/useWorkspace.ts \
        frontend/src/App.tsx
git commit -m "feat(frontend): add workspace context for mode switching

- Creates WorkspaceContext with mode, org, school state
- Persists to localStorage for session continuity
- Provides useWorkspace hook for consuming components
- Wraps TeacherLayout with WorkspaceProvider

Enables teacher workspace switching (personal/organization)"
```

---

## Phase 3: Workspace Switcher UI Components

### Task 3.1: Create WorkspaceSwitcher component

**Files:**
- Create: `frontend/src/components/workspace/WorkspaceSwitcher.tsx`
- Create: `frontend/src/components/workspace/PersonalTab.tsx`
- Create: `frontend/src/components/workspace/OrganizationTab.tsx`

**Step 1: Create PersonalTab (simple passthrough)**

Create `frontend/src/components/workspace/PersonalTab.tsx`:

```typescript
import { SidebarGroup } from "@/components/sidebar/SidebarGroup";

interface PersonalTabProps {
  visibleGroups: any[]; // Use existing sidebar groups
}

export function PersonalTab({ visibleGroups }: PersonalTabProps) {
  return (
    <nav className="space-y-1">
      {visibleGroups.map((group, index) => (
        <SidebarGroup key={index} group={group} />
      ))}
    </nav>
  );
}
```

**Step 2: Create OrganizationTab (placeholder)**

Create `frontend/src/components/workspace/OrganizationTab.tsx`:

```typescript
import { useWorkspace } from "@/hooks/useWorkspace";
import { Building2, ChevronRight } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

export function OrganizationTab() {
  const {
    organizations,
    selectedSchool,
    setSelectedOrganization,
    setSelectedSchool,
  } = useWorkspace();

  if (organizations.length === 0) {
    return (
      <div className="px-3 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
        您尚未加入任何機構
      </div>
    );
  }

  // Phase 1: Show organization + school list
  if (!selectedSchool) {
    return (
      <ScrollArea className="h-[calc(100vh-280px)]">
        <div className="space-y-4">
          {organizations.map((org) => (
            <div key={org.id} className="space-y-1">
              {/* Organization header */}
              <div className="px-3 py-1 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                {org.name}
              </div>

              {/* Schools */}
              {org.schools.map((school) => (
                <button
                  key={school.id}
                  onClick={() => {
                    setSelectedOrganization(org);
                    setSelectedSchool(school);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-left transition-all duration-150 group hover:bg-blue-50 dark:hover:bg-blue-900/20 text-slate-700 dark:text-slate-300 hover:text-blue-700 dark:hover:text-blue-300"
                >
                  <Building2 className="h-4 w-4 flex-shrink-0" />
                  <span className="flex-1">{school.name}</span>
                  <ChevronRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          ))}
        </div>
      </ScrollArea>
    );
  }

  // Phase 2: Show school switcher + menu (placeholder for now)
  return (
    <div className="space-y-4">
      <div className="px-3 py-2 text-sm text-slate-600 dark:text-slate-400">
        已選擇: {selectedSchool.name}
        {/* TODO: Add school switcher dropdown in next task */}
      </div>
    </div>
  );
}
```

**Step 3: Create WorkspaceSwitcher**

Create `frontend/src/components/workspace/WorkspaceSwitcher.tsx`:

```typescript
import { useWorkspace } from "@/hooks/useWorkspace";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { User, Building2 } from "lucide-react";
import { PersonalTab } from "./PersonalTab";
import { OrganizationTab } from "./OrganizationTab";

interface WorkspaceSwitcherProps {
  visibleGroups: any[]; // Existing sidebar groups for personal mode
}

export function WorkspaceSwitcher({ visibleGroups }: WorkspaceSwitcherProps) {
  const { mode, setMode } = useWorkspace();

  return (
    <div className="w-full">
      <Tabs
        value={mode}
        onValueChange={(value) => setMode(value as "personal" | "organization")}
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-2 mb-4 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg h-12">
          <TabsTrigger
            value="personal"
            className="data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:text-blue-600 dark:data-[state=active]:text-blue-400 data-[state=active]:shadow-sm transition-all duration-200"
          >
            <User className="h-4 w-4 mr-2" />
            個人
          </TabsTrigger>
          <TabsTrigger
            value="organization"
            className="data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700 data-[state=active]:text-blue-600 dark:data-[state=active]:text-blue-400 data-[state=active]:shadow-sm transition-all duration-200"
          >
            <Building2 className="h-4 w-4 mr-2" />
            機構
          </TabsTrigger>
        </TabsList>

        <TabsContent value="personal" className="mt-0">
          <PersonalTab visibleGroups={visibleGroups} />
        </TabsContent>

        <TabsContent value="organization" className="mt-0">
          <OrganizationTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

**Step 4: Integrate into TeacherLayout**

Modify `frontend/src/components/TeacherLayout.tsx` (around line 80-150, find sidebar render):

```typescript
// Add import at top
import { WorkspaceSwitcher } from "@/components/workspace/WorkspaceSwitcher";
import { useWorkspace } from "@/hooks/useWorkspace";

// Inside component, after visibleGroups definition:
const { setOrganizations, setLoading } = useWorkspace();

// Fetch organizations on mount
useEffect(() => {
  async function fetchOrganizations() {
    try {
      setLoading(true);
      const response = await apiClient.get("/teachers/organizations");
      setOrganizations(response.data.organizations);
    } catch (error) {
      console.error("Failed to fetch organizations:", error);
      setOrganizations([]);
    } finally {
      setLoading(false);
    }
  }

  fetchOrganizations();
}, [setOrganizations, setLoading]);

// Replace existing sidebar content (find nav section) with:
<WorkspaceSwitcher visibleGroups={visibleGroups} />
```

**Step 5: Test in browser**

```bash
npm run dev
```

Navigate to teacher dashboard. You should see:
- [個人] [機構] tabs at top of sidebar
- Personal tab shows existing menu items
- Organization tab shows "您尚未加入任何機構" (if no orgs)
- Tab switching works, mode persists to localStorage

**Step 6: Commit**

```bash
git add frontend/src/components/workspace/ \
        frontend/src/components/TeacherLayout.tsx
git commit -m "feat(ui): add workspace switcher tabs to sidebar

- WorkspaceSwitcher component with Personal/Organization tabs
- PersonalTab shows existing sidebar groups (passthrough)
- OrganizationTab shows org+school list or empty state
- Fetches organizations from API on mount
- Mode switching persists to localStorage

UI matches design spec section 4.1 (Tab Switcher)"
```

---

## Phase 4: School Switcher & Permission Banner

### Task 4.1: Add school switcher dropdown

**Files:**
- Modify: `frontend/src/components/workspace/OrganizationTab.tsx`
- Create: `frontend/src/components/workspace/SchoolSwitcher.tsx`
- Create: `frontend/src/components/workspace/PermissionBanner.tsx`

**Step 1: Create SchoolSwitcher component**

Create `frontend/src/components/workspace/SchoolSwitcher.tsx`:

```typescript
import { useWorkspace } from "@/hooks/useWorkspace";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Building2 } from "lucide-react";

export function SchoolSwitcher() {
  const {
    selectedOrganization,
    selectedSchool,
    setSelectedSchool,
  } = useWorkspace();

  if (!selectedOrganization || !selectedSchool) {
    return null;
  }

  return (
    <div className="px-3 py-2 mb-4 border-b border-slate-200 dark:border-slate-700">
      <Select
        value={selectedSchool.id}
        onValueChange={(schoolId) => {
          const school = selectedOrganization.schools.find(
            (s) => s.id === schoolId
          );
          if (school) {
            setSelectedSchool(school);
          }
        }}
      >
        <SelectTrigger className="h-14 bg-slate-50 dark:bg-slate-800/50 border-2 border-blue-200 dark:border-blue-700 rounded-lg hover:border-blue-400 dark:hover:border-blue-500">
          <div className="flex items-center gap-2 w-full">
            <Building2 className="h-4 w-4 text-blue-600 flex-shrink-0" />
            <div className="flex-1 text-left">
              <div className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                {selectedOrganization.name}
              </div>
              <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                {selectedSchool.name}
              </div>
            </div>
          </div>
        </SelectTrigger>
        <SelectContent>
          {selectedOrganization.schools.map((school) => (
            <SelectItem key={school.id} value={school.id}>
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                {school.name}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
```

**Step 2: Create PermissionBanner**

Create `frontend/src/components/workspace/PermissionBanner.tsx`:

```typescript
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

export function PermissionBanner() {
  return (
    <Alert className="mx-3 mb-4 border-l-4 border-amber-400 bg-amber-50 dark:border-amber-600 dark:bg-amber-900/20">
      <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
      <AlertTitle className="text-sm font-medium text-amber-800 dark:text-amber-300">
        機構教師模式
      </AlertTitle>
      <AlertDescription className="text-xs text-amber-700 dark:text-amber-400">
        可複製課程、派作業、改作業。無法管理班師生關係。
      </AlertDescription>
    </Alert>
  );
}
```

**Step 3: Update OrganizationTab to use new components**

Modify `frontend/src/components/workspace/OrganizationTab.tsx`:

```typescript
import { SchoolSwitcher } from "./SchoolSwitcher";
import { PermissionBanner } from "./PermissionBanner";
import { SidebarItem } from "@/components/sidebar/SidebarItem";
import { Users, BookOpen, ClipboardList, Eye } from "lucide-react";

// ... existing imports and component start ...

// Replace "Phase 2" section with:
// Phase 2: Show school switcher + menu
return (
  <div>
    <SchoolSwitcher />
    <PermissionBanner />

    <nav className="space-y-1">
      <SidebarItem
        icon={Users}
        label="班級"
        path={`/organization/${selectedOrganization.id}/school/${selectedSchool.id}/classrooms`}
        badge={
          <Eye className="h-3.5 w-3.5 text-slate-400" title="唯讀權限" />
        }
      />
      <SidebarItem
        icon={BookOpen}
        label="學校公版教材"
        path={`/organization/${selectedOrganization.id}/school/${selectedSchool.id}/materials`}
      />
      <SidebarItem
        icon={ClipboardList}
        label="作業管理"
        path={`/organization/${selectedOrganization.id}/school/${selectedSchool.id}/assignments`}
      />
    </nav>
  </div>
);
```

**Step 4: Test in browser**

With test account that has organization:
1. Login as owner@duotopia.com
2. Click [機構] tab
3. Click a school (e.g., "南港分校")
4. Should see:
   - School switcher dropdown at top
   - Amber permission banner
   - Menu with 班級 (Eye icon), 學校公版教材, 作業管理

Test school switching:
1. Click dropdown
2. Select different school
3. Menu should re-render
4. Selection persists on page refresh

**Step 5: Commit**

```bash
git add frontend/src/components/workspace/
git commit -m "feat(ui): add school switcher and permission banner

- SchoolSwitcher dropdown for changing selected school
- PermissionBanner shows restricted mode warning
- OrganizationTab Phase 2: switcher + banner + menu items
- Eye icon badge on read-only menu items

UI matches design spec sections 4.3 and 4.4"
```

---

## Phase 5: Testing & Polish

### Task 5.1: Add transition animations

**Files:**
- Modify: `frontend/src/components/workspace/OrganizationTab.tsx`
- Install: framer-motion (if not already)

**Step 1: Install framer-motion**

```bash
cd frontend
npm install framer-motion
```

**Step 2: Add transition to OrganizationTab**

Modify `frontend/src/components/workspace/OrganizationTab.tsx`:

```typescript
import { motion } from "framer-motion";

// Wrap Phase 2 return with motion.div:
return (
  <motion.div
    key={selectedSchool?.id}
    initial={{ opacity: 0, x: -10 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ duration: 0.25, ease: "easeOut" }}
  >
    <SchoolSwitcher />
    <PermissionBanner />

    <nav className="space-y-1">
      {/* ... menu items ... */}
    </nav>
  </motion.div>
);
```

**Step 3: Test animations**

1. Switch between schools in dropdown
2. Should see smooth fade-in animation
3. Duration: 250ms (as per design spec)

**Step 4: Commit**

```bash
git add frontend/src/components/workspace/OrganizationTab.tsx \
        frontend/package.json frontend/package-lock.json
git commit -m "feat(ui): add smooth transitions for school switching

- Add framer-motion animations to OrganizationTab
- 250ms fade-in when school context changes
- Matches design spec animation timing

Improves UX for workspace switching"
```

---

### Task 5.2: Add keyboard navigation

**Files:**
- Modify: `frontend/src/components/workspace/WorkspaceSwitcher.tsx`

**Step 1: Add keyboard event handlers**

Modify `frontend/src/components/workspace/WorkspaceSwitcher.tsx`:

```typescript
import { useEffect, useRef } from "react";

export function WorkspaceSwitcher({ visibleGroups }: WorkspaceSwitcherProps) {
  const { mode, setMode } = useWorkspace();
  const tabsRef = useRef<HTMLDivElement>(null);

  // Keyboard navigation: Ctrl/Cmd + 1/2 for quick switching
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey)) {
        if (e.key === "1") {
          e.preventDefault();
          setMode("personal");
        } else if (e.key === "2") {
          e.preventDefault();
          setMode("organization");
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setMode]);

  return (
    <div className="w-full" ref={tabsRef}>
      {/* Existing Tabs component */}
    </div>
  );
}
```

**Step 2: Test keyboard shortcuts**

1. Press Cmd+1 (Mac) or Ctrl+1 (Windows) → should switch to Personal
2. Press Cmd+2 or Ctrl+2 → should switch to Organization
3. Tab key should move focus between tab triggers

**Step 3: Commit**

```bash
git add frontend/src/components/workspace/WorkspaceSwitcher.tsx
git commit -m "feat(a11y): add keyboard shortcuts for workspace switching

- Cmd/Ctrl + 1: Switch to Personal
- Cmd/Ctrl + 2: Switch to Organization
- Improves keyboard navigation accessibility

Matches design spec accessibility requirements"
```

---

### Task 5.3: Add loading states

**Files:**
- Modify: `frontend/src/components/workspace/OrganizationTab.tsx`

**Step 1: Add loading spinner**

Modify `frontend/src/components/workspace/OrganizationTab.tsx`:

```typescript
import { Loader2 } from "lucide-react";

export function OrganizationTab() {
  const {
    organizations,
    loading,  // Add this
    // ... rest
  } = useWorkspace();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        <span className="ml-2 text-sm text-slate-600 dark:text-slate-400">
          載入中...
        </span>
      </div>
    );
  }

  // ... rest of component
}
```

**Step 2: Test loading state**

Temporarily add delay to API call in TeacherLayout:

```typescript
await new Promise(resolve => setTimeout(resolve, 2000));  // Add this line
const response = await apiClient.get("/teachers/organizations");
```

Should see spinner for 2 seconds. Remove delay after testing.

**Step 3: Commit**

```bash
git add frontend/src/components/workspace/OrganizationTab.tsx
git commit -m "feat(ui): add loading state to organization tab

- Shows spinner while fetching organizations
- Prevents flash of empty state
- Improves perceived performance"
```

---

### Task 5.4: Error handling

**Files:**
- Modify: `frontend/src/components/TeacherLayout.tsx`
- Modify: `frontend/src/components/workspace/OrganizationTab.tsx`

**Step 1: Add error state to context**

Modify `frontend/src/contexts/WorkspaceContext.tsx`:

```typescript
// Add to interface
export interface WorkspaceContextType {
  // ... existing fields
  error: string | null;
  setError: (error: string | null) => void;
}

// Add to provider
const [error, setError] = useState<string | null>(null);

const value: WorkspaceContextType = {
  // ... existing
  error,
  setError,
};
```

**Step 2: Set error on fetch failure**

Modify `frontend/src/components/TeacherLayout.tsx`:

```typescript
const { setOrganizations, setLoading, setError } = useWorkspace();

useEffect(() => {
  async function fetchOrganizations() {
    try {
      setLoading(true);
      setError(null);  // Clear previous error
      const response = await apiClient.get("/teachers/organizations");
      setOrganizations(response.data.organizations);
    } catch (error) {
      console.error("Failed to fetch organizations:", error);
      setOrganizations([]);
      setError("無法載入機構列表，請稍後再試");  // Set error message
    } finally {
      setLoading(false);
    }
  }

  fetchOrganizations();
}, [setOrganizations, setLoading, setError]);
```

**Step 3: Display error in OrganizationTab**

Modify `frontend/src/components/workspace/OrganizationTab.tsx`:

```typescript
import { AlertCircle } from "lucide-react";

export function OrganizationTab() {
  const {
    organizations,
    loading,
    error,  // Add this
    // ... rest
  } = useWorkspace();

  // Add error state before loading check
  if (error) {
    return (
      <div className="px-3 py-8">
        <div className="flex items-start gap-2 p-3 rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800 dark:text-red-300">
            {error}
          </div>
        </div>
      </div>
    );
  }

  // ... rest of component
}
```

**Step 4: Test error state**

Temporarily break the API URL in TeacherLayout:

```typescript
const response = await apiClient.get("/teachers/organizations_BROKEN");
```

Should see red error message. Fix URL after testing.

**Step 5: Commit**

```bash
git add frontend/src/contexts/WorkspaceContext.tsx \
        frontend/src/components/TeacherLayout.tsx \
        frontend/src/components/workspace/OrganizationTab.tsx
git commit -m "feat(error): add error handling for organization fetch

- Add error state to WorkspaceContext
- Display error message in OrganizationTab
- Clear error on retry/success
- Improves error UX with clear messaging"
```

---

## Phase 6: Documentation & Cleanup

### Task 6.1: Update README and docs

**Files:**
- Create: `frontend/src/components/workspace/README.md`
- Modify: `docs/plans/2026-01-26-teacher-workspace-switcher-design.md`

**Step 1: Create component README**

Create `frontend/src/components/workspace/README.md`:

```markdown
# Workspace Switcher Components

Teacher workspace switching system for separating personal and organization contexts.

## Components

### WorkspaceSwitcher
Main component. Renders tab switcher and delegates to PersonalTab or OrganizationTab.

**Usage:**
\`\`\`tsx
<WorkspaceSwitcher visibleGroups={sidebarGroups} />
\`\`\`

### PersonalTab
Shows personal workspace menu (classrooms, students, materials).

### OrganizationTab
Shows organization/school selection and organization workspace menu.

**Phases:**
1. No school selected: Show org+school list
2. School selected: Show school switcher dropdown + menu

### SchoolSwitcher
Dropdown for switching between schools in selected organization.

### PermissionBanner
Amber alert banner explaining restricted permissions in organization mode.

## State Management

Uses `WorkspaceContext` (see `contexts/WorkspaceContext.tsx`).

**State:**
- `mode`: "personal" | "organization"
- `selectedOrganization`: Current org (or null)
- `selectedSchool`: Current school (or null)
- `organizations`: List of orgs from API
- `loading`: Fetch state
- `error`: Error message

**Persistence:** All state persists to localStorage for session continuity.

## Keyboard Shortcuts

- `Cmd/Ctrl + 1`: Switch to Personal
- `Cmd/Ctrl + 2`: Switch to Organization

## API Dependency

**GET /api/teachers/organizations**

Returns:
\`\`\`json
{
  "organizations": [
    {
      "id": "uuid",
      "name": "Org Name",
      "role": "org_admin",
      "schools": [
        {
          "id": "uuid",
          "name": "School Name",
          "role": "school_admin"
        }
      ]
    }
  ]
}
\`\`\`

## Design Reference

See `docs/plans/2026-01-26-teacher-workspace-switcher-design.md`
```

**Step 2: Update design doc with implementation status**

Modify `docs/plans/2026-01-26-teacher-workspace-switcher-design.md` (add at end):

```markdown
---

## Implementation Status

**Status**: ✅ Completed (2026-01-26)

**Implementation Plan**: See `docs/plans/2026-01-26-teacher-workspace-switcher-implementation.md`

### Phases Completed

- [x] Phase 1: Backend API - GET /api/teachers/organizations
- [x] Phase 2: Frontend State Management - WorkspaceContext
- [x] Phase 3: Workspace Switcher UI Components
- [x] Phase 4: School Switcher & Permission Banner
- [x] Phase 5: Testing & Polish
  - [x] Transition animations
  - [x] Keyboard navigation
  - [x] Loading states
  - [x] Error handling
- [x] Phase 6: Documentation & Cleanup

### Files Created

**Backend:**
- `backend/routers/teachers/teacher_organizations.py`
- `backend/tests/test_teacher_organizations.py`

**Frontend:**
- `frontend/src/contexts/WorkspaceContext.tsx`
- `frontend/src/hooks/useWorkspace.ts`
- `frontend/src/components/workspace/WorkspaceSwitcher.tsx`
- `frontend/src/components/workspace/PersonalTab.tsx`
- `frontend/src/components/workspace/OrganizationTab.tsx`
- `frontend/src/components/workspace/SchoolSwitcher.tsx`
- `frontend/src/components/workspace/PermissionBanner.tsx`
- `frontend/src/components/workspace/README.md`

### Next Steps

1. User testing with teachers who have multiple organizations
2. Add analytics tracking for workspace switching patterns
3. Consider adding workspace-specific notifications (Phase 2+)
4. Improve mobile UX with bottom sheet (instead of dropdown)
```

**Step 3: Commit**

```bash
git add frontend/src/components/workspace/README.md \
        docs/plans/2026-01-26-teacher-workspace-switcher-design.md
git commit -m "docs: add component README and update design spec

- Document workspace switcher components and usage
- Update design spec with implementation status
- List all created files and completed phases
- Add next steps for future enhancements"
```

---

## Final Verification Checklist

Before marking complete, verify:

**Backend:**
- [ ] `pytest backend/tests/test_teacher_organizations.py -v` → All pass
- [ ] API returns correct data: `curl localhost:8000/api/teachers/organizations -H "Authorization: Bearer <token>"`

**Frontend:**
- [ ] Tabs switch between Personal and Organization
- [ ] Organization tab shows org+school list (or empty state)
- [ ] Clicking school shows switcher dropdown
- [ ] Permission banner displays correctly
- [ ] Menu items render with correct icons/labels
- [ ] School switching updates menu (re-renders with new context)
- [ ] Mode persists on page refresh (localStorage)
- [ ] Selected school persists on page refresh
- [ ] Keyboard shortcuts work (Cmd/Ctrl + 1/2)
- [ ] Loading spinner shows during fetch
- [ ] Error message displays on fetch failure
- [ ] Smooth transitions when switching schools

**Accessibility:**
- [ ] Tab key navigates through UI elements
- [ ] Focus visible on all interactive elements
- [ ] Screen reader announces tab changes (test with VoiceOver/NVDA)

**Cross-Browser:**
- [ ] Chrome/Edge: All features work
- [ ] Firefox: All features work
- [ ] Safari: All features work

**Mobile (if applicable):**
- [ ] Tabs render correctly on mobile
- [ ] School list scrollable
- [ ] Dropdown accessible on touch devices

---

## Success Metrics

After implementation, measure:
- [ ] **Performance**: Tab switch < 100ms
- [ ] **User Confusion**: 0 reports of "not knowing which mode I'm in"
- [ ] **Adoption**: X% of teachers with org roles use organization mode
- [ ] **Error Rate**: < 1% of workspace switches result in errors

---

## Troubleshooting

**Problem: Organizations not loading**
- Check backend logs: `docker logs <backend-container>`
- Verify API endpoint: `curl localhost:8000/api/teachers/organizations -H "Authorization: Bearer <token>"`
- Check browser console for errors

**Problem: Mode not persisting**
- Check localStorage: `localStorage.getItem('workspace:mode')`
- Verify WorkspaceProvider wraps TeacherLayout
- Check browser console for context errors

**Problem: School switcher not showing**
- Verify selectedSchool is not null in WorkspaceContext
- Check if organizations array has schools
- Inspect React DevTools for state values

**Problem: Animations not smooth**
- Verify framer-motion installed: `npm list framer-motion`
- Check browser performance (disable if low-end device)
- Reduce animation duration in OrganizationTab

---

## Plan Complete

**Total Tasks**: 14 tasks across 6 phases
**Estimated Time**: 6-8 hours (including testing)
**Difficulty**: Medium (UI state management + API integration)

**Next**: Choose execution approach (see below)
