#!/usr/bin/env python3
"""
執行所有 API 測試
"""
import sys
import subprocess
from datetime import datetime

def run_test(test_file, test_name):
    """執行單一測試檔案"""
    print(f"\n{'='*60}")
    print(f"🧪 執行 {test_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 顯示輸出的最後幾行（結果摘要）
        lines = result.stdout.strip().split('\n')
        for line in lines[-10:]:  # 顯示最後10行
            print(line)
        
        # 判斷是否成功
        success = "✅" in result.stdout and "失敗" not in lines[-1]
        return success
        
    except subprocess.TimeoutExpired:
        print(f"❌ 測試超時")
        return False
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        return False

def main():
    """主程式"""
    print("="*60)
    print("🚀 Duotopia API 測試套件")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 定義測試
    tests = [
        ("tests/api/test_teacher_api.py", "教師 API 測試"),
        ("tests/api/test_student_api.py", "學生 API 測試"),
        ("tests/api/test_classroom_api.py", "班級完整功能測試"),
        ("tests/api/test_reorder_api.py", "拖拽排序測試"),
    ]
    
    results = {}
    
    # 執行所有測試
    for test_file, test_name in tests:
        success = run_test(test_file, test_name)
        results[test_name] = success
    
    # 顯示總結
    print("\n" + "="*60)
    print("📊 測試結果總覽")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, success in results.items():
        if success:
            print(f"✅ {test_name}: 通過")
            passed += 1
        else:
            print(f"❌ {test_name}: 失敗")
            failed += 1
    
    print(f"\n總計: {passed} 通過, {failed} 失敗")
    
    # 計算通過率
    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"通過率: {pass_rate:.1f}%")
    
    print("\n" + "="*60)
    if failed == 0:
        print("🎉 所有測試通過！系統運作正常！")
    else:
        print("⚠️ 有測試失敗，請檢查系統")
    print("="*60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())