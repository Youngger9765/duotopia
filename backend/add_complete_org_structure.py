#!/usr/bin/env python3
"""
為新增的 2 個機構（智慧教育中心、全球語言學院）建立完整架構：
- 每個機構：1個 org_admin
- 每個學校：1個 school_admin（校長）+ 2-3個教師
- 每個學校：2-3個班級
- 每個班級：8-12位學生 + 課程作業
"""
import re

seed_file = "/Users/young/project/duotopia/backend/seed_data.py"

with open(seed_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 在 org_admin_teacher 後新增 2 個新機構的管理員
new_org_admins = '''
    # 智慧教育中心管理員
    smart_admin_teacher = Teacher(
        email="smartadmin@duotopia.com",
        name="許管理",
        password_hash=get_password_hash("smartadmin123"),
        is_active=True,
        is_demo=False,
    )

    # 全球語言學院管理員
    global_admin_teacher = Teacher(
        email="globaladmin@duotopia.com",
        name="游管理",
        password_hash=get_password_hash("globaladmin123"),
        is_active=True,
        is_demo=False,
    )
'''

# 找到 org_teacher 定義後插入
pattern = r'(org_teacher = Teacher\([^)]*\))\s*\n'
match = re.search(pattern, content, re.DOTALL)
if match:
    insert_pos = match.end()
    content = content[:insert_pos] + '\n' + new_org_admins + content[insert_pos:]
    print("✅ 新增 2 個機構管理員")

# 2. 更新 db.add_all 包含新管理員
old_add_all = '''    db.add_all(
        [org_owner_teacher, org_admin_teacher, school_admin_teacher, org_teacher]
    )'''

new_add_all = '''    db.add_all(
        [org_owner_teacher, org_admin_teacher, school_admin_teacher, org_teacher,
         smart_admin_teacher, global_admin_teacher]
    )'''

content = content.replace(old_add_all, new_add_all)

# 3. 更新 refresh
old_refresh = '''    db.refresh(org_owner_teacher)
    db.refresh(org_admin_teacher)
    db.refresh(school_admin_teacher)
    db.refresh(org_teacher)
    print("✅ 建立 4 個機構測試帳號")'''

new_refresh = '''    db.refresh(org_owner_teacher)
    db.refresh(org_admin_teacher)
    db.refresh(school_admin_teacher)
    db.refresh(org_teacher)
    db.refresh(smart_admin_teacher)
    db.refresh(global_admin_teacher)
    print("✅ 建立 6 個機構測試帳號")'''

content = content.replace(old_refresh, new_refresh)

# 4. 為新管理員建立訂閱
old_subscription_loop = '''    for teacher in [
        org_owner_teacher,
        org_admin_teacher,
        school_admin_teacher,
        org_teacher,
    ]:'''

new_subscription_loop = '''    for teacher in [
        org_owner_teacher,
        org_admin_teacher,
        school_admin_teacher,
        org_teacher,
        smart_admin_teacher,
        global_admin_teacher,
    ]:'''

content = content.replace(old_subscription_loop, new_subscription_loop)

# 5. 為新機構管理員設定機構關係（在 owner_org_rels 後）
new_admin_rels = '''
    # 智慧教育中心管理員
    smart_admin_org_rel = TeacherOrganization(
        teacher_id=smart_admin_teacher.id,
        organization_id=smart_edu_org.id,
        role="org_admin",
        is_active=True,
    )

    # 全球語言學院管理員
    global_admin_org_rel = TeacherOrganization(
        teacher_id=global_admin_teacher.id,
        organization_id=global_lang_org.id,
        role="org_admin",
        is_active=True,
    )
    db.add_all([smart_admin_org_rel, global_admin_org_rel])
'''

# 在 admin_org_rel 之後插入
pattern = r'(admin_org_rel = TeacherOrganization\([^)]*\))\s*\n\s*db\.add\(admin_org_rel\)'
match = re.search(pattern, content, re.DOTALL)
if match:
    insert_pos = match.end()
    content = content[:insert_pos] + '\n' + new_admin_rels + content[insert_pos:]
    print("✅ 新增機構管理員關係")

# 6. 更新 teacher_names - 為每個學校新增更多教師
old_teacher_names = '''    teacher_names = [
        ("test_main", "林主任", "林主任"),
        ("test_taipei", "陳老師", "陳老師"),
        ("test_taichung", "黃老師", "黃老師"),
        ("excellence_central", "劉教授", "劉教授"),
        ("excellence_east", "張老師", "張老師"),
        ("excellence_west", "吳老師", "吳老師"),
        ("future_main", "蔡老師", "蔡老師"),
        ("future_north", "楊老師", "楊老師"),
        ("future_south", "鄭老師", "鄭老師"),
        ("smart_kaohsiung", "許老師", "許老師"),
        ("smart_zuoying", "賴老師", "賴老師"),
        ("smart_fengshan", "洪老師", "洪老師"),
        ("global_tainan", "游老師", "游老師"),
        ("global_anping", "周老師", "周老師"),
        ("global_yongkang", "鍾老師", "鍾老師"),
    ]'''

new_teacher_names = '''    teacher_names = [
        ("test_main", "林主任", "林主任"),
        ("test_taipei", "陳老師", "陳老師"),
        ("test_taichung", "黃老師", "黃老師"),
        ("excellence_central", "劉教授", "劉教授"),
        ("excellence_east", "張老師", "張老師"),
        ("excellence_west", "吳老師", "吳老師"),
        ("future_main", "蔡老師", "蔡老師"),
        ("future_north", "楊老師", "楊老師"),
        ("future_south", "鄭老師", "鄭老師"),
        # 智慧教育中心 - 高雄校區（校長+2教師）
        ("smart_kaohsiung_principal", "許校長", "許校長"),
        ("smart_kaohsiung_t1", "許老師", "許老師"),
        ("smart_kaohsiung_t2", "賴老師", "賴老師"),
        # 智慧教育中心 - 左營校區（校長+2教師）
        ("smart_zuoying_principal", "洪校長", "洪校長"),
        ("smart_zuoying_t1", "洪老師A", "洪老師A"),
        ("smart_zuoying_t2", "洪老師B", "洪老師B"),
        # 智慧教育中心 - 鳳山校區（校長+2教師）
        ("smart_fengshan_principal", "蘇校長", "蘇校長"),
        ("smart_fengshan_t1", "蘇老師A", "蘇老師A"),
        ("smart_fengshan_t2", "蘇老師B", "蘇老師B"),
        # 全球語言學院 - 台南校區（校長+2教師）
        ("global_tainan_principal", "游校長", "游校長"),
        ("global_tainan_t1", "游老師A", "游老師A"),
        ("global_tainan_t2", "游老師B", "游老師B"),
        # 全球語言學院 - 安平校區（校長+2教師）
        ("global_anping_principal", "周校長", "周校長"),
        ("global_anping_t1", "周老師A", "周老師A"),
        ("global_anping_t2", "周老師B", "周老師B"),
        # 全球語言學院 - 永康校區（校長+2教師）
        ("global_yongkang_principal", "鍾校長", "鍾校長"),
        ("global_yongkang_t1", "鍾老師A", "鍾老師A"),
        ("global_yongkang_t2", "鍾老師B", "鍾老師B"),
    ]'''

content = content.replace(old_teacher_names, new_teacher_names)
print("✅ 為新學校新增教師（每校 3 位：校長+2教師）")

# 7. 更新 school_teacher_mappings
old_mappings = '''    school_teacher_mappings = [
        (school_teachers[0], test_main_school, ["school_admin"]),
        (school_teachers[1], test_taipei_school, ["teacher"]),
        (school_teachers[2], test_taichung_school, ["teacher"]),
        (school_teachers[3], excellence_central_school, ["school_admin"]),
        (school_teachers[4], excellence_east_school, ["teacher"]),
        (school_teachers[5], excellence_west_school, ["teacher"]),
        (school_teachers[6], future_main_school, ["school_admin"]),
        (school_teachers[7], future_north_school, ["teacher"]),
        (school_teachers[8], future_south_school, ["teacher"]),
        (school_teachers[9], smart_kaohsiung_school, ["school_admin"]),
        (school_teachers[10], smart_zuoying_school, ["teacher"]),
        (school_teachers[11], smart_fengshan_school, ["teacher"]),
        (school_teachers[12], global_tainan_school, ["school_admin"]),
        (school_teachers[13], global_anping_school, ["teacher"]),
        (school_teachers[14], global_yongkang_school, ["teacher"]),
    ]'''

new_mappings = '''    school_teacher_mappings = [
        (school_teachers[0], test_main_school, ["school_admin"]),
        (school_teachers[1], test_taipei_school, ["teacher"]),
        (school_teachers[2], test_taichung_school, ["teacher"]),
        (school_teachers[3], excellence_central_school, ["school_admin"]),
        (school_teachers[4], excellence_east_school, ["teacher"]),
        (school_teachers[5], excellence_west_school, ["teacher"]),
        (school_teachers[6], future_main_school, ["school_admin"]),
        (school_teachers[7], future_north_school, ["teacher"]),
        (school_teachers[8], future_south_school, ["teacher"]),
        # 智慧教育中心 - 高雄校區
        (school_teachers[9], smart_kaohsiung_school, ["school_admin"]),
        (school_teachers[10], smart_kaohsiung_school, ["teacher"]),
        (school_teachers[11], smart_kaohsiung_school, ["teacher"]),
        # 智慧教育中心 - 左營校區
        (school_teachers[12], smart_zuoying_school, ["school_admin"]),
        (school_teachers[13], smart_zuoying_school, ["teacher"]),
        (school_teachers[14], smart_zuoying_school, ["teacher"]),
        # 智慧教育中心 - 鳳山校區
        (school_teachers[15], smart_fengshan_school, ["school_admin"]),
        (school_teachers[16], smart_fengshan_school, ["teacher"]),
        (school_teachers[17], smart_fengshan_school, ["teacher"]),
        # 全球語言學院 - 台南校區
        (school_teachers[18], global_tainan_school, ["school_admin"]),
        (school_teachers[19], global_tainan_school, ["teacher"]),
        (school_teachers[20], global_tainan_school, ["teacher"]),
        # 全球語言學院 - 安平校區
        (school_teachers[21], global_anping_school, ["school_admin"]),
        (school_teachers[22], global_anping_school, ["teacher"]),
        (school_teachers[23], global_anping_school, ["teacher"]),
        # 全球語言學院 - 永康校區
        (school_teachers[24], global_yongkang_school, ["school_admin"]),
        (school_teachers[25], global_yongkang_school, ["teacher"]),
        (school_teachers[26], global_yongkang_school, ["teacher"]),
    ]'''

content = content.replace(old_mappings, new_mappings)
print("✅ 更新教師與學校關係（每校 3 位）")

# 8. 更新 classroom_data - 每個新學校 2-3 個班級
old_classroom_data = '''    classroom_data = [
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
        (school_teachers[9], smart_kaohsiung_school, "智慧教育-高雄-AI班", ProgramLevel.A2),
        (school_teachers[10], smart_zuoying_school, "智慧教育-左營-科技班", ProgramLevel.A1),
        (school_teachers[11], smart_fengshan_school, "智慧教育-鳳山-程式班", ProgramLevel.B1),
        (school_teachers[12], global_tainan_school, "全球語言-台南-國際班", ProgramLevel.B2),
        (school_teachers[13], global_anping_school, "全球語言-安平-多語班", ProgramLevel.A2),
        (school_teachers[14], global_yongkang_school, "全球語言-永康-商務班", ProgramLevel.B1),
    ]'''

new_classroom_data = '''    classroom_data = [
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
    ]'''

content = content.replace(old_classroom_data, new_classroom_data)
print("✅ 為新學校新增班級（每校 3 個班）")

# 9. 更新 school_names_prefixes（為學生命名用）
old_prefixes = '''    school_names_prefixes = [
        ("測試總校", test_main_school),
        ("測試台北", test_taipei_school),
        ("測試台中", test_taichung_school),
        ("卓越中央", excellence_central_school),
        ("卓越東區", excellence_east_school),
        ("卓越西區", excellence_west_school),
        ("未來主校", future_main_school),
        ("未來北桃", future_north_school),
        ("未來南桃", future_south_school),
        ("智慧高雄", smart_kaohsiung_school),
        ("智慧左營", smart_zuoying_school),
        ("智慧鳳山", smart_fengshan_school),
        ("全球台南", global_tainan_school),
        ("全球安平", global_anping_school),
        ("全球永康", global_yongkang_school),
    ]'''

new_prefixes = '''    school_names_prefixes = [
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
    ]'''

content = content.replace(old_prefixes, new_prefixes)
print("✅ 更新學校前綴（用於學生命名）")

# 10. 更新學生數量（每個班級 8-12 位）
content = content.replace(
    'num_students = random.randint(5, 8)  # 每個班級 5-8 位學生',
    'num_students = random.randint(8, 12)  # 每個班級 8-12 位學生'
)
print("✅ 更新學生數量（每個班級 8-12 位）")

# 寫回檔案
with open(seed_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "="*60)
print("✅ 完成！已為新機構建立完整架構：")
print("   📊 智慧教育中心：")
print("      - 1 個機構管理員（許管理）")
print("      - 3 所學校，每校 3 位教師（校長+2教師）")
print("      - 每校 3 個班級，每班 8-12 位學生")
print("")
print("   📊 全球語言學院：")
print("      - 1 個機構管理員（游管理）")
print("      - 3 所學校，每校 3 位教師（校長+2教師）")
print("      - 每校 3 個班級，每班 8-12 位學生")
print("="*60)
