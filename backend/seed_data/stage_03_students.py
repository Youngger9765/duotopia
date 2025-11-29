"""
Stage 3: Student Setup
Creates students and assigns them to classrooms
"""
from seed_data.utils import *


def seed_students(db: Session, classrooms_data: dict):
    """
    Stage 3: Create students and assign to classrooms
    
    Args:
        classrooms_data: Dictionary from Stage 2 containing classrooms
        
    Returns:
        dict: Dictionary containing created students
    """
    # Extract needed entities
    demo_class = classrooms_data['demo_class']
    expired_class = classrooms_data['expired_class']
    trial_class = classrooms_data['trial_class']
    miaoli_class1 = classrooms_data['miaoli_class1']
    miaoli_class2 = classrooms_data['miaoli_class2']
    taichung_class1 = classrooms_data['taichung_class1']
    taichung_class2 = classrooms_data['taichung_class2']
    smart_class1 = classrooms_data['smart_class1']
    smart_class2 = classrooms_data['smart_class2']
    global_class1 = classrooms_data['global_class1']
    global_class2 = classrooms_data['global_class2']
    
    # ============ 4. Demo 學生（統一密碼：20120101）============
    common_birthdate = date(2012, 1, 1)
    common_password = get_password_hash("20120101")

    # 五年級A班學生（增加到12位）
    students_5a_names = [
        "王小明",
        "李小美",
        "陳大雄",
        "黃小華",
        "劉心怡",
        "吳志明",
        "許雅婷",
        "鄭建國",
        "林佳慧",
        "張偉強",
        "蔡雅芳",
        "謝志偉",
    ]

    students_5a = []
    for i, name in enumerate(students_5a_names):
        # 所有五年級學生都使用預設密碼
        student = Student(
            name=name,
            email=f"student{i+1}@duotopia.com",
            password_hash=common_password,
            birthdate=common_birthdate,
            student_number=f"S{i+1:03d}",
            target_wpm=random.randint(50, 70),
            target_accuracy=round(random.uniform(0.70, 0.85), 2),
            password_changed=False,
            email_verified=False,  # 所有學生預設都未驗證 email
            email_verified_at=None,
            is_active=True,
        )
        students_5a.append(student)

    # 六年級B班學生（增加到15位）
    students_6b_names = [
        "張志豪",
        "林靜香",
        "測試學生",
        "蔡文傑",
        "謝佩琪",
        "楊智凱",
        "周美玲",
        "高俊宇",
        "羅曉晴",
        "洪志峰",
        "鍾雅筑",
        "施建成",
        "賴文芳",
        "簡志明",
        "余佳蓉",
    ]

    students_6b = []
    for i, name in enumerate(students_6b_names):
        # 只有最後一個學生（余佳蓉）有特殊密碼
        if name == "余佳蓉":
            password_hash = get_password_hash("custom123")
            password_changed = True
        else:
            password_hash = common_password
            password_changed = False

        student = Student(
            name=name,
            email=f"student{i+13}@duotopia.com",
            password_hash=password_hash,
            birthdate=common_birthdate,
            student_number=f"S{i+13:03d}",
            target_wpm=random.randint(65, 85),
            target_accuracy=round(random.uniform(0.80, 0.95), 2),
            password_changed=password_changed,
            email_verified=False,  # 所有學生預設都未驗證 email
            email_verified_at=None,
            is_active=True,
        )
        students_6b.append(student)

    all_students = students_5a + students_6b
    db.add_all(all_students)
    db.commit()
    print(
        f"✅ 建立 {len(all_students)} 位學生（五年級A班{len(students_5a)}位，六年級B班{len(students_6b)}位）"
    )

    # ============ 4. 學生加入班級 ============
    # 五年級A班
    for student in students_5a:
        enrollment = ClassroomStudent(
            classroom_id=classroom_a.id, student_id=student.id, is_active=True
        )
        db.add(enrollment)

    # 六年級B班
    for student in students_6b:
        enrollment = ClassroomStudent(
            classroom_id=classroom_b.id, student_id=student.id, is_active=True
        )
        db.add(enrollment)

    db.commit()
    print("✅ Demo 老師的學生已加入班級")

    # 4.2 為機構班級添加學生
    # 機構初級A班（王校長 @ 總校）
    org_students_a = []
    for i in range(1, 6):  # 5位學生
        student = Student(
            name=f"機構學生A{i}",
            email=f"org_student_a{i}@test.com",
            password_hash=common_password,
            birthdate=common_birthdate,
            student_number=f"ORG-A{i:03d}",
            is_active=True,
        )
        org_students_a.append(student)

    # 機構進階B班（陳老師 @ 台北分校）
    org_students_b = []
    for i in range(1, 9):  # 8位學生
        student = Student(
            name=f"機構學生B{i}",
            email=f"org_student_b{i}@test.com",
            password_hash=common_password,
            birthdate=common_birthdate,
            student_number=f"ORG-B{i:03d}",
            is_active=True,
        )
        org_students_b.append(student)

    all_org_students = org_students_a + org_students_b
    db.add_all(all_org_students)
    db.commit()
    print(f"✅ 建立 {len(all_org_students)} 位機構學生（初級A班5位，進階B班8位）")

    # 4.3 為每個學校的班級創建學生（每個班級 5-8 位學生）
    school_students_all = []
    student_counter = 1000  # 從 1000 開始編號避免衝突

    school_names_prefixes = [
        ("測試總校", test_main_school),
        ("測試台北", test_taipei_school),
        ("測試台中", test_taichung_school),
        ("卓越中央", excellence_central_school),
        ("卓越東區", excellence_east_school),
        ("卓越西區", excellence_west_school),
        ("未來主校", future_main_school),
        ("未來北桃", future_north_school),
        ("未來南桃", future_south_school),
        # 智慧教育中心 - 高雄（3個班）
        ("智高AI入", smart_kaohsiung_school),
        ("智高AI進", smart_kaohsiung_school),
        ("智高程式", smart_kaohsiung_school),
        # 智慧教育中心 - 左營（3個班）
        ("智左科A", smart_zuoying_school),
        ("智左科B", smart_zuoying_school),
        ("智左創客", smart_zuoying_school),
        # 智慧教育中心 - 鳳山（3個班）
        ("智鳳程初", smart_fengshan_school),
        ("智鳳程中", smart_fengshan_school),
        ("智鳳程高", smart_fengshan_school),
        # 全球語言學院 - 台南（3個班）
        ("全南國A", global_tainan_school),
        ("全南國B", global_tainan_school),
        ("全南商務", global_tainan_school),
        # 全球語言學院 - 安平（3個班）
        ("全安多入", global_anping_school),
        ("全安多進", global_anping_school),
        ("全安商英", global_anping_school),
        # 全球語言學院 - 永康（3個班）
        ("全永商A", global_yongkang_school),
        ("全永商B", global_yongkang_school),
        ("全永國際", global_yongkang_school),
    ]

    for idx, (classroom, school) in enumerate(school_classrooms):
        school_prefix, _ = school_names_prefixes[idx]
        num_students = random.randint(8, 12)  # 每個班級 8-12 位學生

        classroom_students = []
        for i in range(1, num_students + 1):
            student = Student(
                name=f"{school_prefix}-學生{i}",
                email=f"school_student_{student_counter}@duotopia.com",
                password_hash=common_password,
                birthdate=common_birthdate,
                student_number=f"SCH-{student_counter:04d}",
                target_wpm=random.randint(50, 80),
                target_accuracy=round(random.uniform(0.70, 0.90), 2),
                password_changed=False,
                email_verified=False,
                email_verified_at=None,
                is_active=True,
            )
            classroom_students.append(student)
            school_students_all.append((student, classroom))
            student_counter += 1

        db.add_all(classroom_students)

    db.commit()
    print(f"✅ 建立 {len(school_students_all)} 位學校學生（每個班級 5-8 位）")

    # 將學生加入對應班級
    for student, classroom in school_students_all:
        enrollment = ClassroomStudent(
            classroom_id=classroom.id, student_id=student.id, is_active=True
        )
        db.add(enrollment)

    # 學生加入機構班級
    for student in org_students_a:
        enrollment = ClassroomStudent(
            classroom_id=org_classroom_a.id, student_id=student.id, is_active=True
        )
        db.add(enrollment)

    for student in org_students_b:
        enrollment = ClassroomStudent(
            classroom_id=org_classroom_b.id, student_id=student.id, is_active=True
        )
        db.add(enrollment)

    db.commit()
    print("✅ 機構學生已加入班級")


    
    # Return created students  
    return {
        'xiaoming': xiaoming,
        'xiaohong': xiaohong,
        'xiaohua': xiaohua,
        'xiaogang': xiaogang,
        'xiaomei': xiaomei,
        'xiaoqiang': xiaoqiang,
        'miaoli_students': miaoli_students,
        'taichung_students': taichung_students,
        'smart_students': smart_students,
        'global_students': global_students,
    }
