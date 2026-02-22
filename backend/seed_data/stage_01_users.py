"""
Stage 1: User and Organization Setup  
Creates teachers, subscriptions, organizations, and schools
"""
from seed_data.utils import *


def seed_users_and_organizations(db: Session):
    """
    Stage 1: Create all teachers, subscriptions, organizations and schools

    Returns:
        dict: Dictionary containing created entities:
            - demo_teacher, expired_teacher, trial_teacher
            - org_owner_teacher, org_admin_teacher, school_admin_teacher, org_teacher
            - smart_admin_teacher, global_admin_teacher
            - organizations, schools
    """
    # ============ 1. Demo 教師 ============
    # 1.1 充值300天的 Demo 教師
    demo_teacher = Teacher(
        email="demo@duotopia.com",
        password_hash=get_password_hash("demo123"),
        name="Demo 老師",
        is_demo=True,
        is_active=True,
        email_verified=True,
        # 🔄 不再使用舊欄位，改用 subscription_periods 表
    )
    db.add(demo_teacher)

    # 1.2 未充值的教師（已驗證但沒有訂閱）
    expired_teacher = Teacher(
        email="expired@duotopia.com",
        password_hash=get_password_hash("demo123"),
        name="過期老師",
        is_demo=False,
        is_active=True,
        email_verified=True,
        # 🔄 不再使用舊欄位，改用 subscription_periods 表
    )
    db.add(expired_teacher)

    # 1.3 剛驗證得到30天試用的教師
    trial_teacher = Teacher(
        email="trial@duotopia.com",
        password_hash=get_password_hash("demo123"),
        name="試用老師",
        is_demo=False,
        is_active=True,
        email_verified=True,
        # 🔄 不再使用舊欄位，改用 subscription_periods 表
    )
    db.add(trial_teacher)

    db.commit()
    print("✅ 建立 3 個教師帳號:")
    print("   - demo@duotopia.com (充值300天)")
    print("   - expired@duotopia.com (未訂閱/已過期)")
    print("   - trial@duotopia.com (30天試用期)")

    # ============ 1.4 創建對應的 subscription_periods ============
    # Demo 老師的訂閱週期（300天，大配額）— 模擬 School 方案
    demo_period = SubscriptionPeriod(
        teacher_id=demo_teacher.id,
        plan_name="School Teachers",
        amount_paid=0,
        quota_total=999999999,  # 無限配額
        quota_used=0,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=300),
        payment_method="manual",
        payment_status="completed",
        status="active",
    )
    db.add(demo_period)

    # Trial 老師的訂閱週期（30天試用）
    trial_period = SubscriptionPeriod(
        teacher_id=trial_teacher.id,
        plan_name="30-Day Trial",
        amount_paid=0,
        quota_total=18000,  # 30天 * 10分鐘/天 * 60秒 = 18000秒
        quota_used=0,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        payment_method="trial",
        payment_status="completed",
        status="active",
    )
    db.add(trial_period)

    # Expired 老師沒有 subscription_period（已過期）

    db.commit()
    print("✅ 建立訂閱週期 (subscription_periods):")
    print("   - demo@duotopia.com: 999999999秒配額（無限）")
    print("   - trial@duotopia.com: 18000秒配額（30天試用）")
    print("   - expired@duotopia.com: 無訂閱週期")

    # ============ 2. 機構測試帳號（4個新帳號）============
    # 🔴 重要：demo, trial, expired 保持為獨立老師，不加入機構

    print("\n🏢 建立機構測試帳號...")

    # 2.1 創建 4 個新教師帳號
    # 機構擁有者
    org_owner_teacher = Teacher(
        email="owner@duotopia.com",
        name="張機構",
        password_hash=get_password_hash("owner123"),
        is_active=True,
        is_demo=False,
    )

    # 機構管理員
    org_admin_teacher = Teacher(
        email="orgadmin@duotopia.com",
        name="李管理",
        password_hash=get_password_hash("orgadmin123"),
        is_active=True,
        is_demo=False,
    )

    # 學校管理員
    school_admin_teacher = Teacher(
        email="schooladmin@duotopia.com",
        name="王校長",
        password_hash=get_password_hash("schooladmin123"),
        is_active=True,
        is_demo=False,
    )

    # 普通教師
    org_teacher = Teacher(
        email="orgteacher@duotopia.com",
        name="陳老師",
        password_hash=get_password_hash("orgteacher123"),
        is_active=True,
        is_demo=False,
    )

    # 智慧教育中心機構管理員
    smart_admin_teacher = Teacher(
        email="smartadmin@duotopia.com",
        name="許管理",
        password_hash=get_password_hash("smartadmin123"),
        is_active=True,
        is_demo=False,
    )

    # 全球語言學院機構管理員
    global_admin_teacher = Teacher(
        email="globaladmin@duotopia.com",
        name="游管理",
        password_hash=get_password_hash("globaladmin123"),
        is_active=True,
        is_demo=False,
    )

    db.add_all(
        [
            org_owner_teacher,
            org_admin_teacher,
            school_admin_teacher,
            org_teacher,
            smart_admin_teacher,
            global_admin_teacher,
        ]
    )
    db.commit()
    db.refresh(org_owner_teacher)
    db.refresh(org_admin_teacher)
    db.refresh(school_admin_teacher)
    db.refresh(org_teacher)
    db.refresh(smart_admin_teacher)
    db.refresh(global_admin_teacher)
    print("✅ 建立 6 個機構測試帳號")

    # 2.2 為機構測試帳號創建訂閱（給予充足配額）
    for teacher in [
        org_owner_teacher,
        org_admin_teacher,
        school_admin_teacher,
        org_teacher,
        smart_admin_teacher,
        global_admin_teacher,
    ]:
        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="School Teachers",  # 使用學校版方案
            amount_paid=660,  # 學校版金額
            quota_total=25000,  # 25000 點配額
            quota_used=0,  # 未使用
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=365),
            payment_method="manual",  # 手動付款（seed data）
            payment_status="paid",  # 已付款
            status="active",  # 啟用中
        )
        db.add(period)
    db.commit()
    print("✅ 為機構測試帳號建立訂閱（365天，25000點配額）")

    # 2.3 創建測試機構（3個）
    test_org = Organization(
        name="test-cram-school",
        display_name="測試補習班",
        description="用於測試多租戶機構階層功能",
        contact_email="contact@test-cram.com",
        contact_phone="+886-2-9999-8888",
        address="新北市板橋區中山路一段100號",
        is_active=True,
    )

    excellence_org = Organization(
        name="excellence-education",
        display_name="卓越教育集團",
        description="專注於雙語教育的連鎖機構",
        contact_email="contact@excellence-edu.com",
        contact_phone="+886-2-2345-6789",
        address="台北市大安區敦化南路二段200號",
        is_active=True,
    )

    future_org = Organization(
        name="future-learning",
        display_name="未來學苑",
        description="創新教學方法的教育機構",
        contact_email="contact@future-learning.com",
        contact_phone="+886-3-8765-4321",
        address="桃園市中壢區中山路300號",
        is_active=True,
    )

    # 新增機構 4: 智慧教育中心
    smart_edu_org = Organization(
        name="smart-education-center",
        display_name="智慧教育中心",
        description="運用科技打造智慧教學環境",
        contact_email="contact@smart-edu.com",
        contact_phone="+886-7-1234-5678",
        address="高雄市前鎮區中山二路150號",
        is_active=True,
    )

    # 新增機構 5: 全球語言學院
    global_lang_org = Organization(
        name="global-language-institute",
        display_name="全球語言學院",
        description="專業的多國語言培訓機構",
        contact_email="contact@global-lang.com",
        contact_phone="+886-6-9876-5432",
        address="台南市東區大學路500號",
        is_active=True,
    )

    db.add_all([test_org, excellence_org, future_org, smart_edu_org, global_lang_org])
    db.commit()
    db.refresh(test_org)
    db.refresh(excellence_org)
    db.refresh(future_org)
    db.refresh(smart_edu_org)
    db.refresh(global_lang_org)
    print("✅ 建立 5 個測試機構: 測試補習班、卓越教育集團、未來學苑、智慧教育中心、全球語言學院")

    # 2.4 設定機構成員
    # 張機構 = 機構擁有者（擁有5個機構）
    owner_org_rels = [
        TeacherOrganization(
            teacher_id=org_owner_teacher.id,
            organization_id=test_org.id,
            role="org_owner",
            is_active=True,
        ),
        TeacherOrganization(
            teacher_id=org_owner_teacher.id,
            organization_id=excellence_org.id,
            role="org_owner",
            is_active=True,
        ),
        TeacherOrganization(
            teacher_id=org_owner_teacher.id,
            organization_id=future_org.id,
            role="org_owner",
            is_active=True,
        ),
        TeacherOrganization(
            teacher_id=org_owner_teacher.id,
            organization_id=smart_edu_org.id,
            role="org_owner",
            is_active=True,
        ),
        TeacherOrganization(
            teacher_id=org_owner_teacher.id,
            organization_id=global_lang_org.id,
            role="org_owner",
            is_active=True,
        ),
    ]
    db.add_all(owner_org_rels)

    # 李管理 = 機構管理員（只管理測試補習班）
    admin_org_rel = TeacherOrganization(
        teacher_id=org_admin_teacher.id,
        organization_id=test_org.id,
        role="org_admin",
        is_active=True,
    )
    db.add(admin_org_rel)

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

    db.commit()
    print("✅ 設定機構成員:")
    print("   - owner@duotopia.com (張機構): org_owner of 5 organizations")
    print("   - orgadmin@duotopia.com (李管理): org_admin of test_org")

    # 2.5 創建分校（每個機構 3 所學校，共 9 所）

    # 測試補習班的 3 所學校
    test_main_school = School(
        organization_id=test_org.id,
        name="test-main-branch",
        display_name="測試補習班-總校",
        description="測試補習班的主要教學據點",
        contact_email="main@test-cram.com",
        contact_phone="+886-2-8888-0001",
        address="新北市板橋區文化路一段100號",
        is_active=True,
    )

    test_taipei_school = School(
        organization_id=test_org.id,
        name="test-taipei-branch",
        display_name="測試補習班-台北分校",
        description="測試補習班台北分校",
        contact_email="taipei@test-cram.com",
        contact_phone="+886-2-6666-0002",
        address="台北市中正區羅斯福路一段50號",
        is_active=True,
    )

    test_taichung_school = School(
        organization_id=test_org.id,
        name="test-taichung-branch",
        display_name="測試補習班-台中分校",
        description="測試補習班台中分校",
        contact_email="taichung@test-cram.com",
        contact_phone="+886-4-7777-0003",
        address="台中市西屯區台灣大道三段600號",
        is_active=True,
    )

    # 卓越教育集團的 3 所學校
    excellence_central_school = School(
        organization_id=excellence_org.id,
        name="excellence-central",
        display_name="卓越教育-中央校區",
        description="卓越教育集團旗艦校區",
        contact_email="central@excellence-edu.com",
        contact_phone="+886-2-2345-1111",
        address="台北市大安區信義路四段100號",
        is_active=True,
    )

    excellence_east_school = School(
        organization_id=excellence_org.id,
        name="excellence-east",
        display_name="卓越教育-東區校區",
        description="卓越教育東區分校",
        contact_email="east@excellence-edu.com",
        contact_phone="+886-2-2345-2222",
        address="台北市南港區研究院路一段200號",
        is_active=True,
    )

    excellence_west_school = School(
        organization_id=excellence_org.id,
        name="excellence-west",
        display_name="卓越教育-西區校區",
        description="卓越教育西區分校",
        contact_email="west@excellence-edu.com",
        contact_phone="+886-2-2345-3333",
        address="台北市士林區中山北路六段300號",
        is_active=True,
    )

    # 未來學苑的 3 所學校
    future_main_school = School(
        organization_id=future_org.id,
        name="future-main",
        display_name="未來學苑-主校區",
        description="未來學苑主要教學中心",
        contact_email="main@future-learning.com",
        contact_phone="+886-3-8765-1111",
        address="桃園市中壢區中山路300號",
        is_active=True,
    )

    future_north_school = School(
        organization_id=future_org.id,
        name="future-north",
        display_name="未來學苑-北桃園校區",
        description="未來學苑北桃園分校",
        contact_email="north@future-learning.com",
        contact_phone="+886-3-8765-2222",
        address="桃園市桃園區經國路400號",
        is_active=True,
    )

    future_south_school = School(
        organization_id=future_org.id,
        name="future-south",
        display_name="未來學苑-南桃園校區",
        description="未來學苑南桃園分校",
        contact_email="south@future-learning.com",
        contact_phone="+886-3-8765-3333",
        address="桃園市平鎮區環南路500號",
        is_active=True,
    )

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
    all_schools = [
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
    ]

    db.add_all(all_schools)
    db.commit()
    for school in all_schools:
        db.refresh(school)
    print("✅ 建立 15 所分校（每個機構 3 所）")

    # 2.6 創建更多教師（每個學校需要至少一個教師）
    # 為了簡化，我們為每個學校創建一個教師
    school_teachers = []
    teacher_names = [
        ("test_main", "林主任", "林主任"),
        ("test_main_director", "王主任", "王主任"),  # 測試補習班-總校 主任
        ("test_taipei", "陳老師", "陳老師"),
        ("test_taichung", "黃老師", "黃老師"),
        ("test_taichung_director", "趙主任", "趙主任"),  # 測試補習班-台中分校 主任
        ("excellence_central", "劉教授", "劉教授"),
        ("excellence_central_director", "孫主任", "孫主任"),  # 卓越教育-中央校區 主任
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
    ]

    for idx, (school_key, name, display_name) in enumerate(teacher_names):
        teacher = Teacher(
            email=f"teacher_{school_key}@duotopia.com",
            name=display_name,
            password_hash=get_password_hash("teacher123"),
            is_active=True,
            is_demo=False,
        )
        school_teachers.append(teacher)
        db.add(teacher)

    db.commit()
    for t in school_teachers:
        db.refresh(t)
    print(f"✅ 建立 {len(school_teachers)} 個學校教師帳號")

    # 為每個教師創建訂閱
    for teacher in school_teachers:
        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="School Teachers",
            amount_paid=660,
            quota_total=25000,
            quota_used=0,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=365),
            payment_method="manual",
            payment_status="paid",
            status="active",
        )
        db.add(period)
    db.commit()
    print("✅ 為學校教師建立訂閱")

    # 2.7 設定教師與學校關係
    school_teacher_mappings = [
        (school_teachers[0], test_main_school, ["school_admin"]),
        (school_teachers[1], test_main_school, ["school_director"]),  # 測試補習班-總校 主任
        (school_teachers[2], test_taipei_school, ["school_admin"]),
        (school_teachers[3], test_taichung_school, ["school_admin"]),
        (
            school_teachers[4],
            test_taichung_school,
            ["school_director"],
        ),  # 測試補習班-台中分校 主任
        (school_teachers[5], excellence_central_school, ["school_admin"]),
        (
            school_teachers[6],
            excellence_central_school,
            ["school_director"],
        ),  # 卓越教育-中央校區 主任
        (school_teachers[7], excellence_east_school, ["school_admin"]),
        (school_teachers[8], excellence_west_school, ["school_admin"]),
        (school_teachers[9], future_main_school, ["school_admin"]),
        (school_teachers[10], future_north_school, ["school_admin"]),
        (school_teachers[11], future_south_school, ["school_admin"]),
        # 智慧教育中心 - 高雄校區
        (school_teachers[12], smart_kaohsiung_school, ["school_admin"]),
        (school_teachers[13], smart_kaohsiung_school, ["teacher"]),
        (school_teachers[14], smart_kaohsiung_school, ["teacher"]),
        # 智慧教育中心 - 左營校區
        (school_teachers[15], smart_zuoying_school, ["school_admin"]),
        (school_teachers[16], smart_zuoying_school, ["teacher"]),
        (school_teachers[17], smart_zuoying_school, ["teacher"]),
        # 智慧教育中心 - 鳳山校區
        (school_teachers[18], smart_fengshan_school, ["school_admin"]),
        (school_teachers[19], smart_fengshan_school, ["teacher"]),
        (school_teachers[20], smart_fengshan_school, ["teacher"]),
        # 全球語言學院 - 台南校區
        (school_teachers[21], global_tainan_school, ["school_admin"]),
        (school_teachers[22], global_tainan_school, ["teacher"]),
        (school_teachers[23], global_tainan_school, ["teacher"]),
        # 全球語言學院 - 安平校區
        (school_teachers[24], global_anping_school, ["school_admin"]),
        (school_teachers[25], global_anping_school, ["teacher"]),
        (school_teachers[26], global_anping_school, ["teacher"]),
        # 全球語言學院 - 永康校區
        (school_teachers[27], global_yongkang_school, ["school_admin"]),
        (school_teachers[28], global_yongkang_school, ["teacher"]),
        (school_teachers[29], global_yongkang_school, ["teacher"]),
    ]

    for teacher, school, roles in school_teacher_mappings:
        rel = TeacherSchool(
            teacher_id=teacher.id,
            school_id=school.id,
            roles=roles,
            is_active=True,
        )
        db.add(rel)

    # 保留原有的機構測試帳號關係
    school_admin_rel = TeacherSchool(
        teacher_id=school_admin_teacher.id,
        school_id=test_main_school.id,
        roles=["school_admin"],
        is_active=True,
    )
    db.add(school_admin_rel)

    teacher_rel = TeacherSchool(
        teacher_id=org_teacher.id,
        school_id=test_taipei_school.id,
        roles=["teacher"],
        is_active=True,
    )
    db.add(teacher_rel)

    db.commit()
    print("✅ 設定教師與學校關係（每個學校至少一個教師）")

    # Return all created entities for next stages
    return {
        "demo_teacher": demo_teacher,
        "expired_teacher": expired_teacher,
        "trial_teacher": trial_teacher,
        "org_owner_teacher": org_owner_teacher,
        "org_admin_teacher": org_admin_teacher,
        "school_admin_teacher": school_admin_teacher,
        "org_teacher": org_teacher,
        "smart_admin_teacher": smart_admin_teacher,
        "global_admin_teacher": global_admin_teacher,
        # Organizations
        "test_org": test_org,
        "excellence_org": excellence_org,
        "future_org": future_org,
        "smart_edu_org": smart_edu_org,
        "global_lang_org": global_lang_org,
        # Schools
        "test_main_school": test_main_school,
        "test_taipei_school": test_taipei_school,
        "test_taichung_school": test_taichung_school,
        "excellence_central_school": excellence_central_school,
        "excellence_east_school": excellence_east_school,
        "excellence_west_school": excellence_west_school,
        "future_main_school": future_main_school,
        "future_north_school": future_north_school,
        "future_south_school": future_south_school,
        "smart_kaohsiung_school": smart_kaohsiung_school,
        "smart_zuoying_school": smart_zuoying_school,
        "smart_fengshan_school": smart_fengshan_school,
        "global_tainan_school": global_tainan_school,
        "global_anping_school": global_anping_school,
        "global_yongkang_school": global_yongkang_school,
        # School teachers list
        "school_teachers": school_teachers,
    }
