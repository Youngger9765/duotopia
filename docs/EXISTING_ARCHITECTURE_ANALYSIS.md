# 現有架構分析：已預留欄位

## 🔍 發現：Classroom 有預留機構欄位

### 現有 Classroom 模型

```python
class Classroom(Base):
    """班級模型"""
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    level = Column(Enum(ProgramLevel), default=ProgramLevel.A1)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    # ✅ 已預留的欄位（目前未使用）
    school = Column(String(255), nullable=True)  # 學校名稱（與 DB 一致，但不使用）
    grade = Column(String(50), nullable=True)   # 年級（與 DB 一致，但不使用）
    academic_year = Column(String(20), nullable=True)  # 學年度（與 DB 一致，但不使用）

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

---

## 💡 這些欄位的意義

### 1. `school` - 學校名稱
- **原始用途**：可能用來標記「這個班級屬於哪個學校」
- **可轉換為**：`organization_name` 或關聯到 `organizations.id`

### 2. `grade` - 年級
- **原始用途**：標記班級年級（如「五年級」）
- **保留用途**：仍然有用，可以標記「這是幾年級的班」

### 3. `academic_year` - 學年度
- **原始用途**：標記學年度（如「2024-2025」）
- **保留用途**：仍然有用，區分不同學年的班級

---

## 🎯 利用現有欄位的設計方案

### 方案 A：直接轉換 `school` 為機構關聯

```sql
-- 不新增欄位，直接改用現有的 school 欄位
-- Step 1: 將 school 欄位改為 UUID 類型（或保持 String 但存 UUID）
ALTER TABLE classrooms RENAME COLUMN school TO organization_id;
ALTER TABLE classrooms ALTER COLUMN organization_id TYPE UUID USING organization_id::uuid;

-- Step 2: 加入外鍵
ALTER TABLE classrooms
ADD CONSTRAINT fk_classroom_organization
FOREIGN KEY (organization_id) REFERENCES organizations(id);

-- Step 3: 新增 branch_id
ALTER TABLE classrooms ADD COLUMN branch_id UUID REFERENCES branches(id);
```

**優點**：
- ✅ 不增加欄位數量
- ✅ 直接利用預留空間
- ✅ 向下相容（舊資料 organization_id = NULL）

**缺點**：
- ❌ 需要改變欄位類型（String → UUID）
- ❌ migration 比較複雜

---

### 方案 B：保留 `school` 為顯示用，新增關聯欄位（推薦）

```sql
-- 保留 school, grade, academic_year 作為「顯示/篩選」用途
-- 新增機構關聯欄位

ALTER TABLE classrooms ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE classrooms ADD COLUMN branch_id UUID REFERENCES branches(id);

-- school, grade, academic_year 繼續保留
-- 用途：
-- - school: 可以填「台北市XX國小」（自由文字）
-- - organization_id: 關聯到機構表（結構化資料）
```

**資料模型**：
```python
class Classroom(Base):
    # 機構關聯（新增）
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=True)
    branch_id = Column(UUID, ForeignKey("branches.id"), nullable=True)

    # 保留原有欄位作為額外資訊
    school = Column(String(255), nullable=True)  # 學校全名（如「台北市XX國小」）
    grade = Column(String(50), nullable=True)   # 年級（如「五年級」）
    academic_year = Column(String(20), nullable=True)  # 學年度（如「113學年度」）
```

**使用情境**：
```python
# 情境 1：機構內的班級
classroom = Classroom(
    name="五年A班",
    organization_id="org-001",  # 均一教育平台
    branch_id="branch-001",      # 台北校區
    school="台北市XX國小",       # 合作學校
    grade="五年級",
    academic_year="113學年度"
)

# 情境 2：獨立老師的班級
classroom = Classroom(
    name="國小英文班",
    organization_id="org-002",  # 王老師個人工作室
    branch_id="branch-002",      # 預設分校
    school=None,                 # 不屬於特定學校
    grade="三~五年級混齡",
    academic_year="113學年度"
)
```

**優點**：
- ✅ 結構化關聯 + 彈性文字資訊兼具
- ✅ migration 簡單（只加欄位）
- ✅ 向下相容 100%
- ✅ 保留原有欄位的意義

---

## 📊 其他表的檢查

### Teacher - 沒有預留欄位
```python
class Teacher(Base):
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    name = Column(String(100))
    # ... 沒有 organization 相關欄位
```

**需要新增**：
```sql
ALTER TABLE teachers ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE teachers ADD COLUMN branch_id UUID REFERENCES branches(id);
ALTER TABLE teachers ADD COLUMN role VARCHAR(20) DEFAULT 'teacher';
```

---

### Student - 沒有預留欄位
```python
class Student(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(255))
    student_number = Column(String(50))
    # ... 沒有 organization 相關欄位
```

**需要新增**：
```sql
ALTER TABLE students ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE students ADD COLUMN branch_id UUID REFERENCES branches(id);
```

---

### Program - 有 is_public 預留欄位

```python
class Program(Base):
    # ...
    is_public = Column(Boolean, nullable=True)  # 是否公開（與 DB 一致，但不使用）
```

**可轉換為**：
```python
# 改用 visibility 取代 is_public
visibility = Column(String(20), default='private')  # 'public', 'organization', 'private'
```

---

## 🎯 推薦的 Migration 策略

### Phase 1: 新增機構層級表

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    plan_type VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Phase 2: 修改現有表（加欄位，nullable）

```sql
-- Teachers
ALTER TABLE teachers ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE teachers ADD COLUMN branch_id UUID REFERENCES branches(id);
ALTER TABLE teachers ADD COLUMN role VARCHAR(20) DEFAULT 'teacher';

-- Classrooms（利用預留欄位）
ALTER TABLE classrooms ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE classrooms ADD COLUMN branch_id UUID REFERENCES branches(id);
-- school, grade, academic_year 保留原樣

-- Students
ALTER TABLE students ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE students ADD COLUMN branch_id UUID REFERENCES branches(id);
```

### Phase 3: 建立多對多關聯表

```sql
CREATE TABLE classroom_teachers (
    classroom_id INTEGER REFERENCES classrooms(id) ON DELETE CASCADE,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'owner',
    can_edit BOOLEAN DEFAULT true,
    can_assign BOOLEAN DEFAULT true,
    can_grade BOOLEAN DEFAULT true,
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (classroom_id, teacher_id)
);

-- 遷移現有資料
INSERT INTO classroom_teachers (classroom_id, teacher_id, role, can_edit, can_assign, can_grade)
SELECT id, teacher_id, 'owner', true, true, true
FROM classrooms
WHERE teacher_id IS NOT NULL;

-- 重新命名 teacher_id 為 created_by
ALTER TABLE classrooms RENAME COLUMN teacher_id TO created_by;
```

---

## ✅ 總結

### 已預留的欄位
| 表 | 欄位 | 狀態 | 建議用途 |
|---|------|------|---------|
| `classrooms` | `school` | ✅ 已存在，未使用 | 保留作為學校名稱（文字） |
| `classrooms` | `grade` | ✅ 已存在，未使用 | 保留作為年級標記 |
| `classrooms` | `academic_year` | ✅ 已存在，未使用 | 保留作為學年度 |
| `programs` | `is_public` | ✅ 已存在，未使用 | 可改為 `visibility` |

### 需要新增的欄位
| 表 | 欄位 | 用途 |
|---|------|------|
| `teachers` | `organization_id` | 所屬機構 |
| `teachers` | `branch_id` | 所屬分校 |
| `teachers` | `role` | 角色權限 |
| `classrooms` | `organization_id` | 所屬機構（新增） |
| `classrooms` | `branch_id` | 所屬分校（新增） |
| `students` | `organization_id` | 所屬機構 |
| `students` | `branch_id` | 所屬分校 |

### Migration 複雜度評估
- 🟢 **低風險**：新增表（organizations, branches）
- 🟢 **低風險**：現有表加 nullable 欄位
- 🟡 **中風險**：classroom_teachers 多對多（需遷移資料）
- 🟢 **低風險**：保留 school, grade, academic_year 原樣

---

**結論**：
1. ✅ Classroom 已有預留欄位，可以保留作為額外資訊
2. ✅ 新增 organization_id, branch_id 不衝突
3. ✅ 向下相容性 100%（nullable 欄位）
4. ✅ Migration 風險低，可分階段執行

**下一步**：基於這些發現，更新架構設計文件。
