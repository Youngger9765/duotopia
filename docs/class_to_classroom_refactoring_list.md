# Class to Classroom Refactoring List

This document lists all occurrences of "class" used in the context of classroom/班級 that need to be changed to "classroom".

## Backend Python Files

### 1. Models (`/models.py`)
- **Line 44**: `created_classes = relationship("Class", back_populates="teacher")` → `created_classrooms`
- **Line 65**: `class_enrollments = relationship("ClassStudent", back_populates="student")` → `classroom_enrollments`
- **Line 82-100**: `class Class(Base):` → `class Classroom(Base):`
  - **Line 83**: `__tablename__ = "classes"` → `__tablename__ = "classrooms"`
  - **Line 96**: `teacher = relationship("User", back_populates="created_classes")` → `back_populates="created_classrooms"`
  - **Line 97**: `school = relationship("School", back_populates="classes")` → `back_populates="classrooms"`
  - **Line 98**: `students = relationship("ClassStudent", back_populates="class_")` → `ClassroomStudent`, `back_populates="classroom"`
  - **Line 99**: `course_mappings = relationship("ClassCourseMapping", back_populates="class_")` → `ClassroomCourseMapping`, `back_populates="classroom"`

- **Line 101-112**: `class ClassStudent(Base):` → `class ClassroomStudent(Base):`
  - **Line 102**: `__tablename__ = "class_students"` → `__tablename__ = "classroom_students"`
  - **Line 105**: `class_id = Column(String, ForeignKey("classes.id"))` → `classroom_id`, `ForeignKey("classrooms.id")`
  - **Line 110**: `class_ = relationship("Class", back_populates="students")` → `classroom = relationship("Classroom", back_populates="students")`
  - **Line 111**: `student = relationship("Student", back_populates="class_enrollments")` → `back_populates="classroom_enrollments"`

- **Line 132**: `class_mappings = relationship("ClassCourseMapping", back_populates="course")` → `classroom_mappings`, `ClassroomCourseMapping`

- **Line 140-151**: `class ClassCourseMapping(Base):` → `class ClassroomCourseMapping(Base):`
  - **Line 141**: `__tablename__ = "class_course_mappings"` → `__tablename__ = "classroom_course_mappings"`
  - **Line 144**: `class_id = Column(String, ForeignKey("classes.id"))` → `classroom_id`, `ForeignKey("classrooms.id")`
  - **Line 149**: `class_ = relationship("Class", back_populates="course_mappings")` → `classroom = relationship("Classroom", back_populates="course_mappings")`
  - **Line 150**: `course = relationship("Course", back_populates="class_mappings")` → `back_populates="classroom_mappings"`

- **Line 80**: `classes = relationship("Class", back_populates="school")` → `classrooms = relationship("Classroom", back_populates="school")`

### 2. Schemas (`/schemas.py`)
- **Line 84**: Comment `# Class Schemas` → `# Classroom Schemas`
- **Line 85-89**: `class ClassBase(BaseModel):` → `class ClassroomBase(BaseModel):`
- **Line 90-91**: `class ClassCreate(ClassBase):` → `class ClassroomCreate(ClassroomBase):`
- **Line 93-98**: `class ClassUpdate(BaseModel):` → `class ClassroomUpdate(BaseModel):`
- **Line 99-108**: `class Class(ClassBase):` → `class Classroom(ClassroomBase):`

### 3. Teacher Routes (`/routers/teachers.py`)
- **Line 22**: `@router.post("/classes", response_model=schemas.Class)` → `/classrooms`, `response_model=schemas.Classroom`
- **Line 23**: `async def create_class(` → `async def create_classroom(`
- **Line 24**: `class_data: schemas.ClassCreate,` → `classroom_data: schemas.ClassroomCreate,`
- **Line 28**: `db_class = models.Class(` → `db_classroom = models.Classroom(`
- **Line 29**: `**class_data.dict(),` → `**classroom_data.dict(),`
- **Line 35**: `@router.get("/classes", response_model=List[schemas.Class])` → `/classrooms`, `List[schemas.Classroom]`
- **Line 36**: `async def get_classes(` → `async def get_classrooms(`
- **Line 40**: `classes = db.query(models.Class).filter(` → `classrooms = db.query(models.Classroom).filter(`
- **Line 41**: `models.Class.teacher_id == current_user.id,` → `models.Classroom.teacher_id`
- **Line 42**: `models.Class.is_active == True` → `models.Classroom.is_active`
- **Line 47**: `@router.post("/classes/{class_id}/students")` → `/classrooms/{classroom_id}/students`
- **Line 49**: `class_id: str,` → `classroom_id: str,`
- **Line 54**: `class_ = db.query(models.Class).filter(` → `classroom = db.query(models.Classroom).filter(`
- **Line 55**: `models.Class.id == class_id,` → `models.Classroom.id == classroom_id,`
- **Line 56**: `models.Class.teacher_id == current_user.id` → `models.Classroom.teacher_id`
- **Line 58**: `if not class_:` → `if not classroom:`
- **Line 63**: `existing = db.query(models.ClassStudent).filter(` → `db.query(models.ClassroomStudent).filter(`
- **Line 64**: `models.ClassStudent.class_id == class_id,` → `models.ClassroomStudent.classroom_id == classroom_id,`
- **Line 65**: `models.ClassStudent.student_id == student_id` → `models.ClassroomStudent.student_id`
- **Line 71**: `enrollment = models.ClassStudent(` → `models.ClassroomStudent(`
- **Line 72**: `class_id=class_id,` → `classroom_id=classroom_id,`

### 4. Student Routes (`/routers/students.py`)
- **Line 114**: `@router.get("/teachers/{teacher_id}/classes")` → `/teachers/{teacher_id}/classrooms`
- **Line 115**: `async def get_teacher_classes(` → `async def get_teacher_classrooms(`
- **Line 120**: `classes = db.query(models.Class).filter(` → `classrooms = db.query(models.Classroom).filter(`
- **Line 121**: `models.Class.teacher_id == teacher_id,` → `models.Classroom.teacher_id`
- **Line 122**: `models.Class.is_active == True` → `models.Classroom.is_active`
- **Line 127**: `@router.get("/classes/{class_id}/students")` → `/classrooms/{classroom_id}/students`
- **Line 128**: `async def get_class_students(` → `async def get_classroom_students(`
- **Line 129**: `class_id: str,` → `classroom_id: str,`
- **Line 133**: `students = db.query(models.Student).join(models.ClassStudent).filter(` → `join(models.ClassroomStudent).filter(`
- **Line 134**: `models.ClassStudent.class_id == class_id` → `models.ClassroomStudent.classroom_id == classroom_id`
- **Line 148**: `class_ids = db.query(models.ClassStudent.class_id).filter(` → `classroom_ids = db.query(models.ClassroomStudent.classroom_id).filter(`
- **Line 149**: `models.ClassStudent.student_id == student_id` → `models.ClassroomStudent.student_id`
- **Line 152**: `courses = db.query(models.Course).join(models.ClassCourseMapping).filter(` → `join(models.ClassroomCourseMapping).filter(`
- **Line 153**: `models.ClassCourseMapping.class_id.in_(class_ids),` → `models.ClassroomCourseMapping.classroom_id.in_(classroom_ids),`

### 5. Admin Routes (`/routers/admin.py`)
- **Line 21**: `from models import User, Student, School, Class, Course, ClassStudent, ClassCourseMapping` → `Classroom`, `ClassroomStudent`, `ClassroomCourseMapping`
- **Line 141**: `total_students += db.query(ClassStudent).filter(ClassStudent.class_id == class_obj.id).count()` → `ClassroomStudent`, `ClassroomStudent.classroom_id`
- **Line 329**: `class_id: Optional[int] = Query(None),` → `classroom_id: Optional[int] = Query(None),`
- **Line 343**: `if class_id:` → `if classroom_id:`
- **Line 344**: Comment `# Join with ClassStudent to filter by class` → `# Join with ClassroomStudent to filter by classroom`
- **Line 345**: `query = query.join(ClassStudent).filter(ClassStudent.class_id == class_id)` → `join(ClassroomStudent).filter(ClassroomStudent.classroom_id == classroom_id)`
- **Line 455**: `db.query(ClassStudent).filter(ClassStudent.student_id == student_id).delete()` → `ClassroomStudent`, `ClassroomStudent.student_id`

### 6. Seed Scripts
#### `/seed.py`
- **Line 60**: `db.query(models.Class).delete()` → `db.query(models.Classroom).delete()`
- **Line 61**: `db.query(models.ClassStudent).delete()` → `db.query(models.ClassroomStudent).delete()`
- **Line 62**: `db.query(models.ClassCourseMapping).delete()` → `db.query(models.ClassroomCourseMapping).delete()`
- **Line 85**: `class_obj = models.Class(` → `classroom_obj = models.Classroom(`
- **Line 121**: `class_idx = i % len(classes)` → `classroom_idx = i % len(classrooms)`
- **Line 124**: `birth_year = 2012 if classes[class_idx].grade_level == "6" else 2013` → `classrooms[classroom_idx].grade_level`
- **Line 140**: `class_student = models.ClassStudent(` → `classroom_student = models.ClassroomStudent(`
- **Line 141**: `class_id=class_obj.id,` → `classroom_id=classroom_obj.id,`
- **Line 162**: `mapping = models.ClassCourseMapping(` → `models.ClassroomCourseMapping(`
- **Line 163**: `class_id=classes[class_idx].id,` → `classroom_id=classrooms[classroom_idx].id,`
- **Line 178**: `class_students = db.query(models.ClassStudent).filter_by(class_id=class_obj.id).all()` → `classroom_students = db.query(models.ClassroomStudent).filter_by(classroom_id=classroom_obj.id).all()`
- **Line 183**: `class_courses = db.query(models.ClassCourseMapping).filter_by(class_id=class_obj.id).all()` → `classroom_courses = db.query(models.ClassroomCourseMapping).filter_by(classroom_id=classroom_obj.id).all()`

#### `/seed_demo.py`
- **Line 18**: `from models import (User, Student, School, Class, Course, ClassStudent,` → `Classroom`, `ClassroomStudent`
- **Line 19**: `ClassCourseMapping, StudentAssignment, Enrollment, Lesson` → `ClassroomCourseMapping`
- **Line 61**: `db.query(ClassStudent).delete()` → `db.query(ClassroomStudent).delete()`
- **Line 62**: `db.query(ClassCourseMapping).delete()` → `db.query(ClassroomCourseMapping).delete()`
- **Line 184**: `class_obj = Class(**class_data)` → `classroom_obj = Classroom(**classroom_data)`
- **Line 243-246**: All `"class_id": classes["..."]` → `"classroom_id": classrooms["..."]`
- **Line 256-259**: All `"class_id": classes["..."]` → `"classroom_id": classrooms["..."]`
- **Line 270**: `class_student = ClassStudent(**enrollment_data)` → `classroom_student = ClassroomStudent(**enrollment_data)`
- **Line 278**: `mapping = ClassCourseMapping(**mapping_data)` → `ClassroomCourseMapping(**mapping_data)`
- **Line 291**: `enrollments_count = db.query(ClassStudent).count()` → `db.query(ClassroomStudent).count()`
- **Line 292**: `mappings_count = db.query(ClassCourseMapping).count()` → `db.query(ClassroomCourseMapping).count()`

### 7. Test Files
#### `/test_full_system.py`
- References to `Class` model and class-related operations need updating

#### `/tests/e2e/test_class_management.py`
- **Line 18**: `class TestClassManagement:` → Keep as is (this is a Python test class)
- **Line 85**: `def test_class_search(self, page: Page):` → `def test_classroom_search(self, page: Page):`
- **Line 103**: `def test_add_class_modal(self, page: Page):` → `def test_add_classroom_modal(self, page: Page):`
- **Line 144**: `def test_class_selection(self, page: Page):` → `def test_classroom_selection(self, page: Page):`
- Various locator strings referencing class items need updating

#### `/tests/e2e/test_all_pages_data_verification.py`
- **Line 125**: `def test_class_management_data(self, page: Page):` → `def test_classroom_management_data(self, page: Page):`
- **Line 130**: `page.goto("http://localhost:5174/teacher/classes")` → `/teacher/classrooms`
- **Line 142**: `class_items = page.locator('[class*="border-b cursor-pointer hover:bg-gray-50"]')` → `classroom_items`
- **Line 201**: `("班級管理", "/teacher/classes", "班級管理"),` → `/teacher/classrooms`

### 8. Migration Files
#### `/alembic/versions/961527981c89_add_student_phone_enrollment_model_and_.py`
- **Line containing**: `sa.Column('class_id', sa.String(), nullable=True),` → `classroom_id`
- **Line containing**: `sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ),` → `['classroom_id'], ['classrooms.id']`

#### `/alembic/versions/a9b14cfefd7c_initial_migration.py`
- Similar changes as above

### 9. Check Scripts
#### `/check_demo.py`
- **Line 7**: `from models import User, Student, School, Class, Course, Lesson, ClassStudent, ClassCourseMapping` → Update imports
- **Line 52**: `enrollments = db.query(ClassStudent).all()` → `ClassroomStudent`
- **Line 58**: `cls = db.query(Class).filter(Class.id == enrollment.class_id).first()` → `Classroom`, `enrollment.classroom_id`
- **Line 59**: `class_name = cls.name if cls else "未知"` → `classroom_name`
- **Line 62**: `mappings = db.query(ClassCourseMapping).all()` → `ClassroomCourseMapping`
- **Line 68**: `cls = db.query(Class).filter(Class.id == mapping.class_id).first()` → `Classroom`, `mapping.classroom_id`

## Frontend TypeScript/React Files

### 1. API Definitions (`/frontend/src/lib/api.ts`)
- **Line 62**: `createClass: (data: any) =>` → `createClassroom: (data: any) =>`
- **Line 63**: `api.post('/api/teachers/classes', data),` → `/api/teachers/classrooms`
- **Line 65**: `getClasses: () =>` → `getClassrooms: () =>`
- **Line 66**: `api.get('/api/teachers/classes'),` → `/api/teachers/classrooms`
- **Line 68**: `getClass: (classId: string) =>` → `getClassroom: (classroomId: string) =>`
- **Line 69**: `api.get('/api/teachers/classes/${classId}'),` → `/api/teachers/classrooms/${classroomId}`
- **Line 71**: `getClassStudents: (classId: string) =>` → `getClassroomStudents: (classroomId: string) =>`
- **Line 72**: `api.get('/api/teachers/classes/${classId}/students'),` → `/api/teachers/classrooms/${classroomId}/students`
- **Line 74**: `updateClass: (classId: string, data: any) =>` → `updateClassroom: (classroomId: string, data: any) =>`
- **Line 75**: `api.put('/api/teachers/classes/${classId}', data),` → `/api/teachers/classrooms/${classroomId}`
- **Line 77**: `deleteClass: (classId: string) =>` → `deleteClassroom: (classroomId: string) =>`
- **Line 78**: `api.delete('/api/teachers/classes/${classId}'),` → `/api/teachers/classrooms/${classroomId}`
- **Line 80**: `addStudentsToClass: (classId: string, studentIds: string[]) =>` → `addStudentsToClassroom: (classroomId: string, studentIds: string[]) =>`
- **Line 81**: `api.post('/api/teachers/classes/${classId}/students', { student_ids: studentIds }),` → `/api/teachers/classrooms/${classroomId}/students`
- **Line 116**: `getTeacherClasses: (teacherId: string) =>` → `getTeacherClassrooms: (teacherId: string) =>`
- **Line 117**: `api.get('/api/students/teachers/${teacherId}/classes'),` → `/api/students/teachers/${teacherId}/classrooms`
- **Line 119**: `getClassStudents: (classId: string) =>` → `getClassroomStudents: (classroomId: string) =>`
- **Line 120**: `api.get('/api/students/classes/${classId}/students'),` → `/api/students/classrooms/${classroomId}/students`
- **Line 173**: `getStudents: (params?: { school_id?: string; class_id?: string; search?: string }) =>` → `classroom_id`
- **Line 192**: `getClassStats: (classId: string) =>` → `getClassroomStats: (classroomId: string) =>`
- **Line 193**: `api.get('/api/teachers/classes/${classId}/stats'),` → `/api/teachers/classrooms/${classroomId}/stats`

### 2. Class Management Page (`/frontend/src/pages/ClassManagement.tsx`)
- **Line 8**: `interface Class {` → `interface Classroom {`
- **Line 37**: `const [selectedClass, setSelectedClass] = useState<Class | null>(null)` → `selectedClassroom`, `setSelectedClassroom`, `<Classroom | null>`
- **Line 38**: `const [showAddClass, setShowAddClass] = useState(false)` → `showAddClassroom`, `setShowAddClassroom`
- **Line 39**: `const [editingClass, setEditingClass] = useState<Class | null>(null)` → `editingClassroom`, `setEditingClassroom`, `<Classroom | null>`
- **Line 42**: `const [searchClassTerm, setSearchClassTerm] = useState('')` → `searchClassroomTerm`, `setSearchClassroomTerm`
- **Line 47**: `const [classes, setClasses] = useState<Class[]>([])` → `classrooms`, `setClassrooms`, `<Classroom[]>`
- **Line 49**: `const [classStudents, setClassStudents] = useState<Record<string, Student[]>>({})` → `classroomStudents`, `setClassroomStudents`
- **Line 53**: `const [classCourses, setClassCourses] = useState<Record<string, string[]>>({` → `classroomCourses`, `setClassroomCourses`
- **Line 60**: `const fetchClasses = async () => {` → `fetchClassrooms`
- **Line 62**: `const response = await teacherApi.getClasses()` → `teacherApi.getClassrooms()`
- **Line 65**: `console.error('Failed to fetch classes:', error)` → `'Failed to fetch classrooms:'`
- **Line 69**: `const fetchClassStudents = async (classId: string) => {` → `fetchClassroomStudents`, `(classroomId: string)`
- **Line 71**: `const response = await teacherApi.getClassStudents(classId)` → `teacherApi.getClassroomStudents(classroomId)`
- **Line 73**: `setClassStudents(prev => ({ ...prev, [classId]: students }))` → `setClassroomStudents`, `[classroomId]`
- **Line 75**: `console.error('Failed to fetch class students:', error)` → `'Failed to fetch classroom students:'`
- **Line 82**: `const filteredClasses = classes.filter(cls => {` → `filteredClassrooms = classrooms.filter`
- **Line 88**: `const currentClassStudents = selectedClass ? (classStudents[selectedClass.id] || []) : []` → `currentClassroomStudents`, `selectedClassroom`, `classroomStudents[selectedClassroom.id]`
- All other references to `class`, `classes`, `selectedClass`, `editingClass`, `classStudents`, `classCourses` need similar updates

### 3. Other Frontend Files
Similar pattern needs to be applied to any other frontend files that reference class in the context of classroom.

## Database Schema Changes

1. Rename table `classes` to `classrooms`
2. Rename table `class_students` to `classroom_students`
3. Rename table `class_course_mappings` to `classroom_course_mappings`
4. Rename column `class_id` to `classroom_id` in relevant tables
5. Update all foreign key constraints

## Notes

- Do NOT change:
  - Python `class` keyword (class definitions)
  - CSS `class` or React `className` attributes
  - The word "class" when used in other contexts
- Only change "class" when it refers to a classroom/班級
- Update all import statements accordingly
- Update all API endpoints from `/classes` to `/classrooms`
- Update all variable names, function names, and comments
- Create a new migration file to handle the database schema changes