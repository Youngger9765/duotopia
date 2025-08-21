#!/usr/bin/env python3
"""
執行所有後端測試的腳本
可以選擇執行特定類型的測試（單元測試、整合測試、E2E測試）
"""
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd):
    """執行命令並返回結果"""
    print(f"執行命令: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description='執行 Duotopia 後端測試')
    parser.add_argument(
        '--type',
        choices=['unit', 'integration', 'e2e', 'all'],
        default='all',
        help='要執行的測試類型'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='產生測試覆蓋率報告'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='顯示詳細輸出'
    )
    parser.add_argument(
        '--file',
        '-f',
        help='執行特定測試檔案'
    )
    
    args = parser.parse_args()
    
    # 基本 pytest 命令
    base_cmd = "python -m pytest"
    
    # 加入詳細輸出
    if args.verbose:
        base_cmd += " -v"
    
    # 加入覆蓋率
    if args.coverage:
        base_cmd += " --cov=. --cov-report=html --cov-report=term"
    
    # 根據測試類型決定路徑
    if args.file:
        test_cmd = f"{base_cmd} {args.file}"
    elif args.type == 'unit':
        test_cmd = f"{base_cmd} tests/unit/"
    elif args.type == 'integration':
        test_cmd = f"{base_cmd} tests/integration/"
    elif args.type == 'e2e':
        test_cmd = f"{base_cmd} tests/e2e/"
    else:
        test_cmd = f"{base_cmd} tests/"
    
    print("\n" + "="*60)
    print(f"🧪 執行 {args.type} 測試")
    print("="*60 + "\n")
    
    # 執行測試
    exit_code = run_command(test_cmd)
    
    if exit_code == 0:
        print("\n✅ 所有測試通過！")
        if args.coverage:
            print("📊 覆蓋率報告已產生在 htmlcov/index.html")
    else:
        print("\n❌ 測試失敗！")
        sys.exit(exit_code)

if __name__ == "__main__":
    main()