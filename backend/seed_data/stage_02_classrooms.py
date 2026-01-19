"""
Stage 2: Classroom Setup
Creates classrooms for all teachers
"""
from seed_data.utils import *


def seed_classrooms(db: Session, users_data: dict):
    """
    Stage 2: Create classrooms

    Args:
        users_data: Dictionary from Stage 1 containing teachers and schools

    Returns:
        dict: Dictionary containing created classrooms
    """
    # Extract needed entities from previous stage
    demo_teacher = users_data["demo_teacher"]
    expired_teacher = users_data["expired_teacher"]
    trial_teacher = users_data["trial_teacher"]
    org_owner_teacher = users_data["org_owner_teacher"]
    org_admin_teacher = users_data["org_admin_teacher"]
    school_admin_teacher = users_data["school_admin_teacher"]
    org_teacher = users_data["org_teacher"]
    smart_admin_teacher = users_data["smart_admin_teacher"]
    global_admin_teacher = users_data["global_admin_teacher"]
    miaoli_school1 = users_data["miaoli_school1"]
    miaoli_school2 = users_data["miaoli_school2"]
    taichung_school1 = users_data["taichung_school1"]
    taichung_school2 = users_data["taichung_school2"]
    smart_center1 = users_data["smart_center1"]
    smart_center2 = users_data["smart_center2"]
    global_branch1 = users_data["global_branch1"]
    global_branch2 = users_data["global_branch2"]

    # ============ 3. 班級資料 ============

    # 3.1 Demo 老師的班級（獨立，不屬於任何機構/學校）
    classroom_a = Classroom(
        name="五年級A班",
        description="國小五年級英語基礎班",
        level=ProgramLevel.A1,
        teacher_id=demo_teacher.id,
        is_active=True,
    )

    classroom_b = Classroom(
        name="六年級B班",
        description="國小六年級英語進階班",
        level=ProgramLevel.A2,
        teacher_id=demo_teacher.id,
        is_active=True,
    )

    db.add_all([classroom_a, classroom_b])
    db.commit()
    db.refresh(classroom_a)
    db.refresh(classroom_b)
    print("✅ 建立 demo 老師的獨立班級: 五年級A班、六年級B班（不屬於機構）")

    # 3.2 為每個學校創建班級
    school_classrooms = []
    classroom_data = [
        (school_teachers[0], test_main_school, "測試補習班-總校-A1班", ProgramLevel.A1),
        (school_teachers[1], test_taipei_school, "測試補習班-台北-A2班", ProgramLevel.A2),
        (school_teachers[2], test_taichung_school, "測試補習班-台中-B1班", ProgramLevel.B1),
        (
            school_teachers[3],
            excellence_central_school,
            "卓越教育-中央-高級班",
            ProgramLevel.B2,
        ),
        (
            school_teachers[4],
            excellence_east_school,
            "卓越教育-東區-初級班",
            ProgramLevel.A1,
        ),
        (
            school_teachers[5],
            excellence_west_school,
            "卓越教育-西區-進階班",
            ProgramLevel.A2,
        ),
        (school_teachers[6], future_main_school, "未來學苑-主校-創新班", ProgramLevel.A2),
        (
            school_teachers[7],
            future_north_school,
            "未來學苑-北桃園-探索班",
            ProgramLevel.A1,
        ),
        (school_teachers[8], future_south_school, "未來學苑-南桃園-實驗班", ProgramLevel.B1),
        # 智慧教育中心 - 高雄校區（3個班）
        (school_teachers[9], smart_kaohsiung_school, "智慧高雄-AI入門班", ProgramLevel.A1),
        (school_teachers[10], smart_kaohsiung_school, "智慧高雄-AI進階班", ProgramLevel.A2),
        (school_teachers[11], smart_kaohsiung_school, "智慧高雄-程式班", ProgramLevel.B1),
        # 智慧教育中心 - 左營校區（3個班）
        (school_teachers[12], smart_zuoying_school, "智慧左營-科技A班", ProgramLevel.A1),
        (school_teachers[13], smart_zuoying_school, "智慧左營-科技B班", ProgramLevel.A2),
        (school_teachers[14], smart_zuoying_school, "智慧左營-創客班", ProgramLevel.B1),
        # 智慧教育中心 - 鳳山校區（3個班）
        (school_teachers[15], smart_fengshan_school, "智慧鳳山-程式初級", ProgramLevel.A1),
        (school_teachers[16], smart_fengshan_school, "智慧鳳山-程式中級", ProgramLevel.A2),
        (school_teachers[17], smart_fengshan_school, "智慧鳳山-程式高級", ProgramLevel.B2),
        # 全球語言學院 - 台南校區（3個班）
        (school_teachers[18], global_tainan_school, "全球台南-國際A班", ProgramLevel.A1),
        (school_teachers[19], global_tainan_school, "全球台南-國際B班", ProgramLevel.A2),
        (school_teachers[20], global_tainan_school, "全球台南-商務班", ProgramLevel.B2),
        # 全球語言學院 - 安平校區（3個班）
        (school_teachers[21], global_anping_school, "全球安平-多語入門", ProgramLevel.A1),
        (school_teachers[22], global_anping_school, "全球安平-多語進階", ProgramLevel.A2),
        (school_teachers[23], global_anping_school, "全球安平-商務英語", ProgramLevel.B1),
        # 全球語言學院 - 永康校區（3個班）
        (school_teachers[24], global_yongkang_school, "全球永康-商務A班", ProgramLevel.A2),
        (school_teachers[25], global_yongkang_school, "全球永康-商務B班", ProgramLevel.B1),
        (school_teachers[26], global_yongkang_school, "全球永康-國際班", ProgramLevel.B2),
    ]

    for teacher, school, classroom_name, level in classroom_data:
        classroom = Classroom(
            name=classroom_name,
            description=f"{school.display_name}的班級",
            level=level,
            teacher_id=teacher.id,
            is_active=True,
        )
        school_classrooms.append((classroom, school))
        db.add(classroom)

    db.commit()
    for classroom, _ in school_classrooms:
        db.refresh(classroom)
    print(f"✅ 建立 {len(school_classrooms)} 個學校班級（每個學校一個班級）")

    # 3.3 將班級綁定到學校
    for classroom, school in school_classrooms:
        classroom_school = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=school.id,
            is_active=True,
        )
        db.add(classroom_school)

    # 保留原有的機構測試帳號班級
    org_classroom_a = Classroom(
        name="機構初級A班",
        description="測試補習班初級英語班",
        level=ProgramLevel.A1,
        teacher_id=school_admin_teacher.id,
        is_active=True,
    )

    org_classroom_b = Classroom(
        name="機構進階B班",
        description="測試補習班進階英語班",
        level=ProgramLevel.A2,
        teacher_id=org_teacher.id,
        is_active=True,
    )

    db.add_all([org_classroom_a, org_classroom_b])
    db.commit()
    db.refresh(org_classroom_a)
    db.refresh(org_classroom_b)

    org_classroom_a_school = ClassroomSchool(
        classroom_id=org_classroom_a.id,
        school_id=test_main_school.id,
        is_active=True,
    )
    org_classroom_b_school = ClassroomSchool(
        classroom_id=org_classroom_b.id,
        school_id=test_taipei_school.id,
        is_active=True,
    )
    db.add_all([org_classroom_a_school, org_classroom_b_school])

    db.commit()
    print("✅ 班級綁定到學校完成")

    # 3.4 測試場景：創建一個 inactive 的分校 (測試 soft delete)
    inactive_school = School(
        organization_id=test_org.id,
        name="old-branch",
        display_name="舊分校",
        description="已關閉的分校（用於測試 soft delete）",
        is_active=False,  # Soft deleted
    )
    db.add(inactive_school)
    db.commit()
    print("✅ 額外測試場景: 舊分校 (is_active=False)")

    print("\n📝 重要提醒:")
    print("   - demo, trial, expired 三個帳號保持為獨立老師")
    print("   - 機構測試使用 4 個新帳號: owner, orgadmin, schooladmin, orgteacher")

    # Return created classrooms
    return {
        "demo_class": demo_class,
        "expired_class": expired_class,
        "trial_class": trial_class,
        "miaoli_class1": miaoli_class1,
        "miaoli_class2": miaoli_class2,
        "taichung_class1": taichung_class1,
        "taichung_class2": taichung_class2,
        "smart_class1": smart_class1,
        "smart_class2": smart_class2,
        "global_class1": global_class1,
        "global_class2": global_class2,
    }
