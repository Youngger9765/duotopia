#!/usr/bin/env python3
"""
為 seed_data.py 新增 2 個機構，每個機構 3 所學校
"""
import re

seed_file = "/Users/young/project/duotopia/backend/seed_data.py"

# 讀取原始檔案
with open(seed_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 在 future_south_school 後新增 6 所學校
schools_addition = '''
    # 智慧教育中心的 3 所學校
    smart_kaohsiung_school = School(
        organization_id=smart_edu_org.id,
        name="smart-kaohsiung",
        display_name="智慧教育-高雄校區",
        description="智慧教育中心高雄主校區",
        contact_email="kaohsiung@smart-edu.com",
        contact_phone="+886-7-1234-1111",
        address="高雄市前鎮區中山二路150號",
        is_active=True,
    )

    smart_zuoying_school = School(
        organization_id=smart_edu_org.id,
        name="smart-zuoying",
        display_name="智慧教育-左營校區",
        description="智慧教育中心左營分校",
        contact_email="zuoying@smart-edu.com",
        contact_phone="+886-7-1234-2222",
        address="高雄市左營區博愛二路200號",
        is_active=True,
    )

    smart_fengshan_school = School(
        organization_id=smart_edu_org.id,
        name="smart-fengshan",
        display_name="智慧教育-鳳山校區",
        description="智慧教育中心鳳山分校",
        contact_email="fengshan@smart-edu.com",
        contact_phone="+886-7-1234-3333",
        address="高雄市鳳山區光復路一段300號",
        is_active=True,
    )

    # 全球語言學院的 3 所學校
    global_tainan_school = School(
        organization_id=global_lang_org.id,
        name="global-tainan",
        display_name="全球語言-台南校區",
        description="全球語言學院台南主校區",
        contact_email="tainan@global-lang.com",
        contact_phone="+886-6-9876-1111",
        address="台南市東區大學路500號",
        is_active=True,
    )

    global_anping_school = School(
        organization_id=global_lang_org.id,
        name="global-anping",
        display_name="全球語言-安平校區",
        description="全球語言學院安平分校",
        contact_email="anping@global-lang.com",
        contact_phone="+886-6-9876-2222",
        address="台南市安平區安平路600號",
        is_active=True,
    )

    global_yongkang_school = School(
        organization_id=global_lang_org.id,
        name="global-yongkang",
        display_name="全球語言-永康校區",
        description="全球語言學院永康分校",
        contact_email="yongkang@global-lang.com",
        contact_phone="+886-6-9876-3333",
        address="台南市永康區中華路700號",
        is_active=True,
    )
'''

# 找到 future_south_school 定義結束的位置
pattern = r'(future_south_school = School\([^)]*\))\s*\n'
match = re.search(pattern, content, re.DOTALL)
if match:
    insert_pos = match.end()
    content = content[:insert_pos] + '\n' + schools_addition + content[insert_pos:]
    print("✅ 新增 6 所學校定義")

# 2. 更新 all_schools 列表
old_all_schools = '''    all_schools = [
        test_main_school,
        test_taipei_school,
        test_taichung_school,
        excellence_central_school,
        excellence_east_school,
        excellence_west_school,
        future_main_school,
        future_north_school,
        future_south_school,
    ]'''

new_all_schools = '''    all_schools = [
        test_main_school,
        test_taipei_school,
        test_taichung_school,
        excellence_central_school,
        excellence_east_school,
        excellence_west_school,
        future_main_school,
        future_north_school,
        future_south_school,
        smart_kaohsiung_school,
        smart_zuoying_school,
        smart_fengshan_school,
        global_tainan_school,
        global_anping_school,
        global_yongkang_school,
    ]'''

content = content.replace(old_all_schools, new_all_schools)
print("✅ 更新 all_schools 列表")

# 3. 更新學校數量提示
content = content.replace(
    'print("✅ 建立 9 所分校（每個機構 3 所）")',
    'print("✅ 建立 15 所分校（每個機構 3 所）")'
)

# 4. 新增 6 個教師
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
        ("smart_kaohsiung", "許老師", "許老師"),
        ("smart_zuoying", "賴老師", "賴老師"),
        ("smart_fengshan", "洪老師", "洪老師"),
        ("global_tainan", "游老師", "游老師"),
        ("global_anping", "周老師", "周老師"),
        ("global_yongkang", "鍾老師", "鍾老師"),
    ]'''

content = content.replace(old_teacher_names, new_teacher_names)
print("✅ 新增 6 個教師")

# 5. 更新 school_teacher_mappings
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
        (school_teachers[9], smart_kaohsiung_school, ["school_admin"]),
        (school_teachers[10], smart_zuoying_school, ["teacher"]),
        (school_teachers[11], smart_fengshan_school, ["teacher"]),
        (school_teachers[12], global_tainan_school, ["school_admin"]),
        (school_teachers[13], global_anping_school, ["teacher"]),
        (school_teachers[14], global_yongkang_school, ["teacher"]),
    ]'''

content = content.replace(old_mappings, new_mappings)
print("✅ 更新教師與學校關係")

# 6. 更新 classroom_data
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
        (school_teachers[9], smart_kaohsiung_school, "智慧教育-高雄-AI班", ProgramLevel.A2),
        (school_teachers[10], smart_zuoying_school, "智慧教育-左營-科技班", ProgramLevel.A1),
        (school_teachers[11], smart_fengshan_school, "智慧教育-鳳山-程式班", ProgramLevel.B1),
        (school_teachers[12], global_tainan_school, "全球語言-台南-國際班", ProgramLevel.B2),
        (school_teachers[13], global_anping_school, "全球語言-安平-多語班", ProgramLevel.A2),
        (school_teachers[14], global_yongkang_school, "全球語言-永康-商務班", ProgramLevel.B1),
    ]'''

content = content.replace(old_classroom_data, new_classroom_data)
print("✅ 新增 6 個班級")

# 寫回檔案
with open(seed_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ 完成！已為 owner@duotopia.com 新增 2 個機構（智慧教育中心、全球語言學院）")
print("   每個機構 3 所學校，每所學校有 1 個教師和 1 個班級")
