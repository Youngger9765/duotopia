# 學校學生管理功能完整設計文檔

**創建日期**: 2026-01-19  
**更新日期**: 2026-01-20  
**狀態**: 設計完成，待實現  
**相關功能**: 機構層級管理 > 學校管理 > 學生管理

---

## 📋 目錄

1. [概述](#概述)
2. [核心設計理念](#核心設計理念)
3. [Teacher 場域切換機制](#teacher-場域切換機制)
4. [權限限制規則](#權限限制規則)
5. [數據模型設計](#數據模型設計)
6. [API 設計](#api-設計)
7. [前端設計](#前端設計)
8. [實現步驟](#實現步驟)
9. [Migration 計劃](#migration-計劃)
10. [衝突分析與解決方案](#衝突分析與解決方案)

---

## 概述

實現學校層級的學生管理功能，支持學生與學校、學生與班級的多對多關係。

### 核心原則

1. **學生在學校層級管理**：學生屬於學校，而不是直接屬於班級
2. **多對多關係**：學生可以同時屬於多個學校、多個班級
3. **流程**：先在學校建立學生名冊 → 再分配到班級

---

## 核心設計理念

### 1. 學生與學校關係：多對多 ⭐

**業務場景**：
- 學生可能同時在多個學校就讀（補習班多校區、跨校選課、不同課程在不同學校）
- 轉校但保留原校記錄

**設計決策**：
- ✅ 使用 `StudentSchool` 關聯表（多對多）
- ❌ **不使用** `Student.school_id`（單一歸屬）

### 2. 學生與班級關係：多對多

- ✅ 一個學生可以同時屬於多個班級
- ✅ 一個班級可以有多個學生
- ⚠️ **約束**：如果學生在班級 A，則班級 A 所屬的學校必須是學生所屬的學校之一

### 3. 學生與組織關係：間接

- ❌ 學生**不直接**屬於 Organization
- ✅ 通過 `Student → StudentSchool → School → Organization` 間接關聯
- ✅ 機構層級查詢只需一次 JOIN：`Student → School → Organization`

**為什麼不直接關聯 Organization？**

| 方案 | 優點 | 缺點 |
|------|------|------|
| **學生只屬於 School** ⭐ | ✅ 符合業務邏輯<br>✅ 查詢效率高<br>✅ 數據一致性 | ⚠️ 機構層級查詢需一次 JOIN |
| 學生只屬於 Organization | ✅ 機構層級查詢直接 | ❌ 學校歸屬不直接<br>❌ 未分配班級的學生無法確定學校<br>❌ 違反業務邏輯 |
| 同時屬於兩者 | ✅ 多層級直接查詢 | ❌ 需要維護一致性<br>❌ 數據冗餘 |

---

## Teacher 場域切換機制

### 🎯 核心概念

Teacher 可以在「機構任教」和「個人場域」兩種模式之間切換。在不同模式下，Teacher 的操作權限不同。

#### 1. **個人場域（Personal Mode）** 🏠
- **定義**：Teacher 作為獨立教師運作
- **權限**：
  - ✅ 可以創建/編輯/刪除自己的班級
  - ✅ 可以創建/編輯/刪除自己的學生（散戶）
  - ✅ 完全自主管理
- **班級類型**：個人班級（沒有 `ClassroomSchool` 關係）
- **學生類型**：散戶學生（沒有 `StudentSchool` 關係）

#### 2. **機構任教（Organization Mode）** 🏫
- **定義**：Teacher 在機構/學校中任教
- **權限**：
  - ❌ **不能**創建/編輯/刪除學校的班級
  - ❌ **不能**創建/編輯/刪除學校的學生
  - ✅ 只能查看自己任教的班級和學生
  - ✅ 可以批改作業、查看進度等教學活動
- **班級類型**：學校班級（有 `ClassroomSchool` 關係）
- **學生類型**：學校學生（有 `StudentSchool` 關係）
- **管理方式**：所有 CRUD 操作必須通過學校後台進行

### 🔄 場景切換機制

**UI 設計建議**：
```
┌─────────────────────────────────┐
│  教學場域                       │
│  [個人場域] [機構任教] ← 切換按鈕 │
└─────────────────────────────────┘
```

**切換邏輯**：
1. 從「個人場域」切換到「機構任教」：Teacher 必須至少屬於一個學校
2. 從「機構任教」切換到「個人場域」：直接切換，恢復所有個人場域的操作權限

**狀態儲存**：
```typescript
interface TeacherContext {
  mode: "personal" | "organization";
  currentSchoolId?: string; // 僅在 organization 模式下
}
```

---

## 權限限制規則

### 規則 1: 個人場域下的限制

**允許的操作**：
- ✅ `POST /api/teachers/classrooms` - 創建個人班級
- ✅ `PUT /api/teachers/classrooms/{id}` - 編輯個人班級
- ✅ `DELETE /api/teachers/classrooms/{id}` - 刪除個人班級
- ✅ `POST /api/teachers/students` - 創建散戶學生
- ✅ `PUT /api/teachers/students/{id}` - 編輯散戶學生
- ✅ `DELETE /api/teachers/students/{id}` - 刪除散戶學生

**限制**：
- ❌ 不能操作屬於學校的班級（有 `ClassroomSchool` 關係）
- ❌ 不能操作屬於學校的學生（有 `StudentSchool` 關係）

### 規則 2: 機構任教下的限制

**允許的操作**：
- ✅ `GET /api/teachers/classrooms` - 查看自己任教的班級（只讀）
- ✅ `GET /api/teachers/students` - 查看自己班級的學生（只讀）
- ✅ `GET /api/teachers/classrooms/{id}` - 查看班級詳情
- ✅ `GET /api/teachers/students/{id}` - 查看學生詳情
- ✅ 所有教學活動相關的操作（批改作業、查看進度等）

**禁止的操作**：
- ❌ `POST /api/teachers/classrooms` - 如果當前模式是機構任教，且班級會屬於學校
- ❌ `PUT /api/teachers/classrooms/{id}` - 編輯學校班級
- ❌ `DELETE /api/teachers/classrooms/{id}` - 刪除學校班級
- ❌ `POST /api/teachers/students` - 在學校班級中創建學生
- ❌ `PUT /api/teachers/students/{id}` - 編輯學校學生
- ❌ `DELETE /api/teachers/students/{id}` - 刪除學校學生

**替代方案**：
- 所有 CRUD 操作必須通過學校後台：
  - `POST /api/schools/{school_id}/classrooms`
  - `POST /api/schools/{school_id}/students`
  - 等學校層級 API

### 核心檢查邏輯

**後端權限檢查函數**：

```python
def check_classroom_is_personal(classroom_id: int, db: Session) -> bool:
    """
    檢查班級是否為個人班級（不屬於任何學校）
    
    Returns:
        True: 個人班級
        False: 學校班級
    """
    from models import ClassroomSchool
    
    classroom_school = db.query(ClassroomSchool).filter(
        ClassroomSchool.classroom_id == classroom_id,
        ClassroomSchool.is_active.is_(True)
    ).first()
    
    return classroom_school is None


def check_student_is_personal(student_id: int, db: Session) -> bool:
    """
    檢查學生是否為散戶（不屬於任何學校）
    
    Returns:
        True: 散戶學生
        False: 學校學生
    """
    from models import StudentSchool
    
    student_school = db.query(StudentSchool).filter(
        StudentSchool.student_id == student_id,
        StudentSchool.is_active.is_(True)
    ).first()
    
    return student_school is None
```

**Teacher 端 API 檢查範例**：

```python
@router.post("/api/teachers/students")
async def create_student(...):
    if student_data.classroom_id:
        classroom = db.query(Classroom).filter(...).first()
        
        # 檢查班級是否屬於學校
        if not check_classroom_is_personal(classroom.id, db):
            raise HTTPException(
                status_code=403,
                detail="此班級屬於學校，請通過學校後台創建學生"
            )
    
    # 個人班級：正常創建散戶學生
    ...

@router.put("/api/teachers/classrooms/{id}")
async def update_classroom(...):
    classroom = db.query(Classroom).filter(...).first()
    
    # 檢查班級是否屬於學校
    if not check_classroom_is_personal(classroom.id, db):
        raise HTTPException(
            status_code=403,
            detail="此班級屬於學校，請通過學校後台編輯"
        )
    
    # 個人班級：正常編輯
    ...
```

### 📋 需要修改的端點清單

**Teacher 端需要添加檢查的端點**：

1. **班級管理**：
   - [ ] `POST /api/teachers/classrooms` - 檢查模式
   - [ ] `PUT /api/teachers/classrooms/{id}` - 檢查班級是否為個人班級
   - [ ] `DELETE /api/teachers/classrooms/{id}` - 檢查班級是否為個人班級

2. **學生管理**：
   - [ ] `POST /api/teachers/students` - 檢查班級是否為個人班級
   - [ ] `PUT /api/teachers/students/{id}` - 檢查學生是否為散戶
   - [ ] `DELETE /api/teachers/students/{id}` - 檢查學生是否為散戶
   - [ ] `POST /api/teachers/classrooms/{id}/students/batch` - 檢查班級是否為個人班級
   - [ ] `POST /api/teachers/students/batch-import` - 檢查班級是否為個人班級

3. **只讀操作（不需要修改）**：
   - ✅ `GET /api/teachers/classrooms` - 允許查看所有班級
   - ✅ `GET /api/teachers/students` - 允許查看所有學生
   - ✅ `GET /api/teachers/classrooms/{id}` - 允許查看班級詳情
   - ✅ `GET /api/teachers/students/{id}` - 允許查看學生詳情

### 🎯 業務場景示例

**場景 1: 獨立教師（個人場域）**
```
Teacher A（獨立教師）
├─ 個人場域模式
├─ 創建「我的班級 1」
│  └─ 創建散戶學生：張三、李四
└─ 完全自主管理 ✅
```

**場景 2: 學校教師（機構任教）**
```
Teacher B（學校教師）
├─ 機構任教模式（學校 A）
├─ 查看學校分配的班級「一年級 A 班」
│  └─ 只能查看學生（只讀）
├─ 不能創建班級 ❌
├─ 不能創建學生 ❌
└─ 所有管理操作 → 學校後台 ✅
```

**場景 3: 混合模式（未來擴展）**
```
Teacher C
├─ 個人場域：管理自己的補習班學生
└─ 機構任教：在學校 A 任教（只讀訪問）
```

---

## 數據模型設計

### 完整關係結構

```
Organization (一對多) School (多對多) Student
                                    ↓ (多對多)
                               Classroom

關係表：
1. Organization → School (一對多)
   - School.organization_id ✅ 已存在

2. School ↔ Student (多對多) ⚠️ 需要新增
   - StudentSchool 關聯表（新增）

3. School → Classroom (一對多)
   - ClassroomSchool 關聯表 ✅ 已存在

4. Student ↔ Classroom (多對多)
   - ClassroomStudent 關聯表 ✅ 已存在
```

### 新增：StudentSchool 關聯表

```python
class StudentSchool(Base):
    """學生-學校關聯表（多對多）"""
    
    __tablename__ = "student_schools"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False, index=True)
    school_id = Column(UUID, ForeignKey('schools.id'), nullable=False, index=True)
    
    # 狀態
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # 時間戳記
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="school_enrollments")
    school = relationship("School", back_populates="student_enrollments")
    
    # 唯一約束：一個學生在一個學校只能有一條記錄
    __table_args__ = (
        UniqueConstraint("student_id", "school_id", name="uq_student_school"),
        Index("ix_student_schools_active", "student_id", "school_id", "is_active"),
    )
```

### 更新：Student 模型

```python
class Student(Base):
    # ... 現有欄位 ...
    
    # Relationships
    school_enrollments = relationship("StudentSchool", back_populates="student")  # 新增
    classroom_enrollments = relationship("ClassroomStudent", back_populates="student")
    assignments = relationship("StudentAssignment", back_populates="student")
```

### 更新：School 模型

```python
class School(Base):
    # ... 現有欄位 ...
    
    # Relationships
    organization = relationship("Organization", back_populates="schools")
    teacher_schools = relationship("TeacherSchool", back_populates="school", ...)
    classroom_schools = relationship("ClassroomSchool", back_populates="school", ...)
    student_enrollments = relationship("StudentSchool", back_populates="school")  # 新增
```

### 業務規則

1. **學生-學校關係**
   - ✅ 一個學生可以同時屬於多個學校
   - ✅ 一個學校可以有多個學生
   - ✅ 學生可以暫時不屬於任何學校（未分配狀態）

2. **學生-班級關係**
   - ✅ 一個學生可以同時屬於多個班級
   - ⚠️ **約束**：如果學生在班級 A，則班級 A 所屬的學校必須是學生所屬的學校之一

3. **驗證邏輯**
   ```python
   def validate_student_classroom_relationship(
       student_id: int,
       classroom_id: int,
       db: Session
   ) -> bool:
       """驗證學生是否可以加入班級"""
       # 1. 獲取班級所屬的學校
       classroom_school = db.query(ClassroomSchool).filter(
           ClassroomSchool.classroom_id == classroom_id,
           ClassroomSchool.is_active.is_(True)
       ).first()
       
       if not classroom_school:
           return False
       
       school_id = classroom_school.school_id
       
       # 2. 檢查學生是否屬於該學校
       student_school = db.query(StudentSchool).filter(
           StudentSchool.student_id == student_id,
           StudentSchool.school_id == school_id,
           StudentSchool.is_active.is_(True)
       ).first()
       
       return student_school is not None
   ```

---

## API 設計

### 1. 獲取學校所有學生

```
GET /api/schools/{school_id}/students
```

**權限**：school_admin, org_admin, org_owner

**查詢參數**：
- `page` (optional): 分頁
- `limit` (optional): 每頁數量
- `search` (optional): 搜索關鍵字（姓名、學號、email）
- `status` (optional): 狀態過濾（active/inactive）
- `classroom_id` (optional): 過濾特定班級的學生
- `unassigned` (optional): true/false，只顯示未分配的學生

**返回格式**：
```json
[
  {
    "id": 1,
    "name": "張三",
    "email": "zhang@example.com",
    "student_number": "001",
    "birthdate": "2010-01-01",
    "is_active": true,
    "last_login": "2026-01-19T10:00:00Z",
    "schools": [
      {"id": "uuid-1", "name": "學校 A"},
      {"id": "uuid-2", "name": "學校 B"}
    ],
    "classrooms": [
      {"id": 5, "name": "一年級 A 班", "school_id": "uuid-1"},
      {"id": 6, "name": "數學進階班", "school_id": "uuid-2"}
    ]
  }
]
```

### 2. 在學校創建學生

```
POST /api/schools/{school_id}/students
```

**權限**：school_admin, org_admin, org_owner

**Request Body**:
```json
{
  "name": "string",
  "email": "string (optional)",
  "student_number": "string (optional)",
  "birthdate": "YYYY-MM-DD",
  "phone": "string (optional)"
}
```

**業務邏輯**：
1. 創建 Student 記錄
2. 同時創建 StudentSchool 關聯（student_id, school_id）

### 3. 添加已存在的學生到學校

```
POST /api/schools/{school_id}/students/{student_id}
```

**權限**：school_admin, org_admin, org_owner

**業務邏輯**：如果學生已存在但不屬於該學校，創建 StudentSchool 關聯

### 4. 更新學生資訊

```
PUT /api/schools/{school_id}/students/{student_id}
```

**權限**：school_admin, org_admin, org_owner

**Request Body**:
```json
{
  "name": "string (optional)",
  "email": "string (optional)",
  "student_number": "string (optional)",
  "birthdate": "YYYY-MM-DD (optional)",
  "phone": "string (optional)",
  "is_active": "boolean (optional)"
}
```

### 5. 添加學生到班級（多對多）

```
POST /api/schools/{school_id}/students/{student_id}/classrooms
```

**權限**：school_admin, org_admin, org_owner

**Request Body**:
```json
{
  "classroom_id": 5
}
```

**業務邏輯**：
1. **驗證學生屬於班級所在的學校**（重要！）
2. 檢查學生是否已經在該班級（避免重複）
3. 如果不存在，創建新的 `ClassroomStudent` 關聯
4. 驗證 `classroom_id` 屬於該學校
5. 如果已存在且 `is_active=false`，則設為 `true`

### 6. 從班級移除學生

```
DELETE /api/schools/{school_id}/students/{student_id}/classrooms/{classroom_id}
```

**權限**：school_admin, org_admin, org_owner

**業務邏輯**：軟刪除 `ClassroomStudent` 關聯（設 `is_active=false`）

### 7. 批量添加學生到班級

```
POST /api/schools/{school_id}/classrooms/{classroom_id}/students/batch
```

**權限**：school_admin, org_admin, org_owner

**Request Body**:
```json
{
  "student_ids": [1, 2, 3]
}
```

**業務邏輯**：為每個學生創建 `ClassroomStudent` 關聯（如果已存在則跳過）

### 8. 獲取班級學生列表

```
GET /api/schools/{school_id}/classrooms/{classroom_id}/students
```

**權限**：school_admin, org_admin, org_owner

**返回**：該班級的所有學生

### 9. 從學校移除學生

```
DELETE /api/schools/{school_id}/students/{student_id}
```

**權限**：school_admin, org_admin, org_owner

**業務邏輯**：軟刪除 `StudentSchool` 關聯（設 `is_active=false`）

**注意**：同時需要處理該學生在該學校所有班級的關聯

### 10. 批量導入學生

```
POST /api/schools/{school_id}/students/batch-import
```

**權限**：school_admin, org_admin, org_owner

**Request Body**:
```json
{
  "students": [
    {
      "name": "string",
      "email": "string (optional)",
      "student_number": "string (optional)",
      "birthdate": "YYYY-MM-DD",
      "phone": "string (optional)",
      "classroom_id": 5
    }
  ],
  "duplicate_action": "skip|update|add_suffix"
}
```

### 權限檢查函數

```python
def check_school_student_permission(
    teacher_id: int, 
    school_id: uuid.UUID, 
    db: Session
) -> bool:
    """檢查是否有管理學校學生的權限"""
    # org_owner, org_admin: 允許
    # school_admin: 允許
    # teacher: 不允許（只能查看自己班級的學生）

def check_student_in_school(
    student_id: int,
    school_id: uuid.UUID,
    db: Session
) -> bool:
    """檢查學生是否屬於學校（多對多關係）"""
    student_school = db.query(StudentSchool).filter(
        StudentSchool.student_id == student_id,
        StudentSchool.school_id == school_id,
        StudentSchool.is_active.is_(True)
    ).first()
    return student_school is not None

def check_classroom_in_school(
    classroom_id: int,
    school_id: uuid.UUID,
    db: Session
) -> bool:
    """檢查班級是否屬於學校"""
    classroom_school = db.query(ClassroomSchool).filter(
        ClassroomSchool.classroom_id == classroom_id,
        ClassroomSchool.school_id == school_id,
        ClassroomSchool.is_active.is_(True)
    ).first()
    return classroom_school is not None
```

---

## 前端設計

### 用戶流程

#### 場景 1: 創建學生名冊
```
組織管理 > 學校詳情 > [學生管理] > 建立學生
URL: /organization/schools/:schoolId/students
```

#### 場景 2: 從班級添加學生
```
組織管理 > 學校詳情 > 班級管理 > [某班級] > [添加學生] > 選擇學校學生列表
```

#### 場景 3: 管理學生班級歸屬
```
組織管理 > 學校詳情 > [學生管理] > [學生列表] > [指派班級]
```

### 頁面組件

```
frontend/src/pages/organization/
  └─ SchoolStudentsPage.tsx  # 學校學生管理頁面
```

### 共享組件

```
frontend/src/components/organization/
  ├─ StudentListTable.tsx         # 學生列表表格（顯示班級信息）
  ├─ CreateStudentDialog.tsx      # 創建學生對話框
  ├─ EditStudentDialog.tsx        # 編輯學生對話框
  ├─ AssignClassroomDialog.tsx    # 指派班級對話框
  ├─ SelectStudentsDialog.tsx     # 選擇學生對話框（從班級頁面調用）
  └─ ImportStudentsDialog.tsx     # 批量導入對話框
```

### 路由

```typescript
// 學校學生管理
<Route 
  path="schools/:schoolId/students" 
  element={<SchoolStudentsPage />} 
/>

// 班級學生列表（在班級詳情頁中）
<Route 
  path="schools/:schoolId/classrooms/:classroomId/students" 
  element={<ClassroomStudentsListPage />} 
/>
```

### 學校學生管理頁面布局

```
┌─────────────────────────────────────────────────┐
│  Breadcrumb: 組織 > 學校 > 學生管理             │
├─────────────────────────────────────────────────┤
│  [學校名稱] 的學生名冊                           │
│  [添加學生] [批量導入] [導出]                    │
├─────────────────────────────────────────────────┤
│  搜索: [_________]  狀態: [全部▼]  班級: [全部▼] │
├─────────────────────────────────────────────────┤
│  ☑ 姓名   學號   Email  生日  班級  狀態  操作  │
│  ☑ 張三   001    ...    2000  A班,B班 ✅ [編輯][添加][移除]│
│  ☑ 李四   002    ...    2001  未分配 ✅  [編輯][添加]│
└─────────────────────────────────────────────────┘
```

### 在學校詳情頁添加「學生管理」按鈕

```
SchoolDetailPage 中：
┌─────────────────────────────┐
│  學校詳情                    │
│                             │
│  [編輯學校] [邀請教師]      │
│                             │
│  管理功能：                  │
│  [班級管理] [教師管理]      │
│  [學生管理] [教材管理]      │
└─────────────────────────────┘
```

---

## 實現步驟

### Phase 1: 數據模型修改（Task 1）

**Task 1**: 創建 `StudentSchool` 關聯表（多對多）
- 創建 Migration（見下方 Migration 計劃）
- 更新 Student 和 School 模型定義
- 添加關聯關係

### Phase 2: Backend API（Tasks 2-7）

**Task 2**: 創建 Schemas
- `SchoolStudentCreate`
- `SchoolStudentUpdate`
- `AddStudentToSchoolRequest`
- `AssignClassroomRequest`
- `BatchAssignRequest`
- `BatchStudentImport`

**Task 3**: 實現權限檢查函數
- `check_school_student_permission()`
- `check_student_in_school()`（通過 StudentSchool）
- `check_classroom_in_school()`
- `validate_student_classroom_school()`（驗證學生-班級-學校關係）

**Task 4**: 實現 GET 端點
- `GET /api/schools/{school_id}/students`
- `GET /api/schools/{school_id}/classrooms/{classroom_id}/students`

**Task 5**: 實現 POST 端點
- `POST /api/schools/{school_id}/students`（創建學生並添加到學校）
- `POST /api/schools/{school_id}/students/{student_id}`（添加已存在學生到學校）
- `POST /api/schools/{school_id}/students/batch-import`
- `POST /api/schools/{school_id}/classrooms/{classroom_id}/students/batch`

**Task 6**: 實現 PUT/POST/DELETE 端點
- `PUT /api/schools/{school_id}/students/{student_id}`
- `POST /api/schools/{school_id}/students/{student_id}/classrooms`（添加班級）
- `DELETE /api/schools/{school_id}/students/{student_id}/classrooms/{classroom_id}`（移除班級）

**Task 7**: 實現 DELETE 端點
- `DELETE /api/schools/{school_id}/students/{student_id}`（從學校移除學生）
- `DELETE /api/schools/{school_id}/classrooms/{classroom_id}/students/{student_id}`（從班級移除學生）

### Phase 3: Frontend（Tasks 8-11）

**Task 8**: 創建 API Client 方法
- 在 `api.ts` 中添加所有學生管理方法

**Task 9**: 創建學校學生管理頁面
- `SchoolStudentsPage.tsx`
- 整合 `StudentListTable` 組件

**Task 10**: 創建對話框組件
- `CreateStudentDialog.tsx`
- `EditStudentDialog.tsx`
- `AssignClassroomDialog.tsx`
- `SelectStudentsDialog.tsx`
- `ImportStudentsDialog.tsx`

**Task 11**: 更新現有頁面
- 在 `SchoolDetailPage` 添加「學生管理」按鈕
- 在 `SchoolClassroomsPage` 添加班級學生列表入口
- 在班級頁面添加「添加學生」功能

### Phase 4: Testing（Tasks 12-13）

**Task 12**: 編寫 Backend 測試
- 權限測試
- CRUD 操作測試
- 多對多關係測試（一個學生可以屬於多個班級）

**Task 13**: 前端整合測試
- 完整流程測試
- 錯誤處理測試

---

## Migration 計劃

### 簡化原因 ⭐

**機構/學校功能尚未上線**，因此：
- ❌ 沒有 `ClassroomSchool` 舊數據需要遷移
- ❌ 不需要複雜的數據遷移邏輯
- ✅ **只需要創建空的 `student_schools` 表**

### Migration 數量

需要創建：**1 個 Migration 文件**（非常簡單）

### Migration 詳細內容

**名稱**：`20260119_XXXX_create_student_school_relationship.py`  
**Base Revision**：`84e62a916eea` (make_classroom_teacher_id_nullable)

#### 1. 創建 `student_schools` 表

```python
op.create_table(
    'student_schools',
    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('school_id', sa.UUID(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('enrolled_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
    sa.UniqueConstraint('student_id', 'school_id', name='uq_student_school'),
    sa.PrimaryKeyConstraint('id')
)
```

#### 2. 創建索引

```python
op.create_index('ix_student_schools_student_id', 'student_schools', ['student_id'])
op.create_index('ix_student_schools_school_id', 'student_schools', ['school_id'])
op.create_index(
    'ix_student_schools_active',
    'student_schools',
    ['student_id', 'school_id', 'is_active']
)
```

#### 3. ~~數據遷移~~ ⚠️ **不需要**

因為機構/學校功能尚未上線，沒有舊數據需要遷移。

**後續行為**：
- 當學校管理員在學校創建學生時，會同時創建 `StudentSchool` 記錄
- 當將學生添加到班級時，如果學生不屬於該學校，會自動創建 `StudentSchool` 記錄

#### 4. Downgrade 邏輯

```python
def downgrade() -> None:
    # 刪除索引
    op.drop_index('ix_student_schools_active', table_name='student_schools')
    op.drop_index('ix_student_schools_school_id', table_name='student_schools')
    op.drop_index('ix_student_schools_student_id', table_name='student_schools')
    
    # 刪除表
    op.drop_table('student_schools')
```

### 完整的 Migration 代碼示例

```python
"""create_student_school_relationship

Revision ID: XXXX
Revises: 84e62a916eea
Create Date: 2026-01-19 XX:XX:XX

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'XXXX'
down_revision: Union[str, None] = '84e62a916eea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create student_schools table
    op.create_table(
        'student_schools',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column(
            'enrolled_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'school_id', name='uq_student_school'),
    )
    
    # Create indexes
    op.create_index(
        'ix_student_schools_student_id',
        'student_schools',
        ['student_id'],
        unique=False
    )
    op.create_index(
        'ix_student_schools_school_id',
        'student_schools',
        ['school_id'],
        unique=False
    )
    op.create_index(
        'ix_student_schools_active',
        'student_schools',
        ['student_id', 'school_id', 'is_active'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_student_schools_active', table_name='student_schools')
    op.drop_index('ix_student_schools_school_id', table_name='student_schools')
    op.drop_index('ix_student_schools_student_id', table_name='student_schools')
    
    # Drop table
    op.drop_table('student_schools')
```

### 受影響的模型文件（非 Migration）

需要更新的模型文件（不屬於 migration，但需要同時更新）：

1. **`backend/models/organization.py`**
   - 創建新的 `StudentSchool` 模型類

2. **`backend/models/user.py`**
   - 在 `Student` 類中添加 `school_enrollments` relationship

3. **`backend/models/organization.py`**（School 類）
   - 在 `School` 類中添加 `student_enrollments` relationship

### 執行步驟

1. **創建 Migration 文件**
   ```bash
   cd backend
   alembic revision -m "create_student_school_relationship"
   ```

2. **編寫 Migration 內容**
   - 複製上面的代碼
   - 更新 revision ID

3. **更新模型文件**
   - 創建 `StudentSchool` 模型
   - 更新 `Student` 和 `School` 模型

4. **測試 Migration**
   ```bash
   # 測試 upgrade
   alembic upgrade head
   
   # 測試 downgrade
   alembic downgrade -1
   
   # 再次 upgrade
   alembic upgrade head
   ```

5. **驗證**
   - 檢查表是否創建成功
   - 檢查索引是否創建成功
   - 測試插入記錄

### 優勢

由於沒有舊數據：
- ✅ **Migration 極其簡單**：只需要創建表結構
- ✅ **無風險**：不會影響現有數據
- ✅ **無需測試複雜的遷移邏輯**
- ✅ **快速完成**：30 分鐘內可完成

---

## 技術考慮

### 1. 數據一致性
- 添加班級前，**必須驗證學生屬於班級所在的學校**（重要約束）
- 添加班級前，檢查是否已存在（避免重複）
- 使用事務確保原子性
- 支持一個學生同時屬於多個學校
- 支持一個學生同時屬於多個班級
- 從學校移除學生時，需要處理該學生在該學校的所有班級關聯

### 2. 性能優化
- 使用 `selectinload` 預加載關聯數據
- 實現分頁避免大量數據查詢
- 批量操作時使用事務

### 3. 錯誤處理
- 學生已存在於該班級時，返回提示（不報錯，視為成功）
- 班級不存在時返回 404
- 權限不足時返回 403
- 學生不屬於該學校時返回 400

### 4. 向後兼容
- 現有教師端學生管理 API 繼續工作
- 學校層級 API 是新增的，不影響現有功能

---

---

## 衝突分析與解決方案

### ✅ 架構理解（已澄清）

#### Teacher 端（散戶模式）
- **Teacher 創建的班級**：個人班級，`Classroom.teacher_id` 有值，**沒有** `ClassroomSchool` 關係
- **Teacher 創建的學生**：散戶學生，只屬於教師個人
- **不應該**創建 `StudentSchool` 關係 ✅

#### 機構/學校端
- **學校創建的班級**：`POST /api/schools/{school_id}/classrooms`，有 `ClassroomSchool` 關係
- **學校創建的學生**：`POST /api/schools/{school_id}/students`，有 `StudentSchool` 關係
- **流程**：先在學校建立學生名冊 → 再分配到班級

### 🔍 實際衝突檢查

#### 場景 1: Teacher 在個人班級創建學生 ✅ 無衝突

**情況**：
- Teacher 通過 `POST /api/teachers/classrooms` 創建班級
- 這個班級沒有 `ClassroomSchool` 關係（個人班級）
- Teacher 通過 `POST /api/teachers/students` 創建學生
- 學生只會創建 `Student` 和 `ClassroomStudent`，沒有 `StudentSchool`

**結論**：✅ **符合設計**，無衝突

#### 場景 2: Teacher 在學校班級創建學生 ⚠️ 需要權限檢查

**問題描述**：
- 學校管理員通過 `POST /api/schools/{school_id}/classrooms` 創建班級
- 這個班級有 `ClassroomSchool` 關係，並且可能指定了 `teacher_id`
- Teacher（作為該班級的導師）嘗試通過 `POST /api/teachers/students` 創建學生
- **但是**：Teacher 端的邏輯只檢查 `Classroom.teacher_id == current_teacher.id`
- 如果這個班級屬於學校，但 Teacher 在 Teacher 端創建學生，**不會創建 StudentSchool**

**解決方案**：
- ✅ 在 Teacher 端創建學生時檢查班級是否屬於學校
- ✅ 如果班級屬於學校，返回 403 錯誤並提示使用學校後台

### 🎯 最終結論

**當前實現**：
- ✅ Teacher 端創建學生不創建 StudentSchool（符合設計）
- ✅ 學校端創建學生創建 StudentSchool（符合設計）
- ⚠️ 但需要添加檢查阻止 Teacher 在學校班級中創建學生

**建議方案：在 Teacher 端創建學生時檢查班級類型**

```python
# backend/routers/teachers/student_ops.py
if student_data.classroom_id:
    classroom = db.query(Classroom).filter(...).first()
    
    # 檢查班級是否屬於學校
    classroom_school = db.query(ClassroomSchool).filter(
        ClassroomSchool.classroom_id == classroom.id,
        ClassroomSchool.is_active.is_(True)
    ).first()
    
    if classroom_school:
        # 班級屬於學校，應該通過學校端創建學生
        raise HTTPException(
            status_code=403,
            detail="此班級屬於學校，請通過學校管理頁面創建學生"
        )
```

這樣可以確保：
- ✅ Teacher 端只能管理個人班級的學生
- ✅ 學校端只能管理學校班級的學生
- ✅ 職責清晰，不會混淆

### ✅ 驗證清單

**測試場景**：

- [ ] Teacher 在個人場域創建班級 → ✅ 成功
- [ ] Teacher 在個人場域創建學生 → ✅ 成功
- [ ] Teacher 嘗試在學校班級中創建學生（Teacher 端）→ ❌ 403 錯誤
- [ ] Teacher 編輯學校班級 → ❌ 403 錯誤
- [ ] Teacher 刪除學校學生 → ❌ 403 錯誤
- [ ] Teacher 查看學校班級和學生 → ✅ 成功（只讀）
- [ ] 學校管理員通過學校後台創建班級 → ✅ 成功
- [ ] 學校管理員通過學校後台創建學生 → ✅ 成功

---

## 總結

### 核心設計

- **學生與學校關係**：多對多（`StudentSchool` 關聯表）
- **學生與班級關係**：多對多（`ClassroomStudent` 關聯表）
- **流程**：先在學校建立學生名冊 → 再分配到班級

### Teacher 場域切換

- **個人場域**：完全自主管理，可 CRUD 個人班級和散戶學生
- **機構任教**：只讀訪問，所有 CRUD 必須通過學校後台

### 權限保護

- ✅ Teacher 端不能操作學校班級和學校學生
- ✅ 後端權限檢查確保數據一致性
- ✅ 清晰的錯誤訊息引導用戶使用正確的操作方式

### 實現規模

- **Migration**：1 個，非常簡單（只需要創建表）
- **API Endpoints**：10 個（學校層級）+ 權限檢查（Teacher 端）
- **前端頁面**：1 個主頁面 + 5 個對話框組件
- **預計實現時間**：Phase 1 (1 天) + Phase 2 (3-4 天) + Phase 3 (3-4 天) + Phase 4 (2 天) = **約 9-11 天**

