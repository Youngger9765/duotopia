"""
E2E 整合測試執行器
提供彩色輸出和詳細報告
"""

import subprocess
import sys
from datetime import datetime


class Colors:
    """終端顏色"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text: str):
    """打印標題"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_section(text: str):
    """打印區塊標題"""
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-' * len(text)}{Colors.ENDC}")


def print_success(text: str):
    """打印成功訊息"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_failure(text: str):
    """打印失敗訊息"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text: str):
    """打印警告訊息"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def run_tests():
    """執行測試"""
    print_header("🧪 E2E 整合測試：訂閱系統重構驗證")

    print_section("📋 測試配置")
    print("  測試文件: test_subscription_integration_full.py")
    print(f"  執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  測試模式: E2E Integration")

    print_section("🚀 開始執行測試...")

    # 執行 pytest
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/e2e/test_subscription_integration_full.py",
        "-v",
        "--tb=short",
        "--color=yes",
        "-s",
    ]

    try:
        result = subprocess.run(cmd, capture_output=False, text=True)

        print_section("📊 測試結果")

        if result.returncode == 0:
            print_success("所有測試通過！")
            print(
                f"\n{Colors.OKGREEN}{Colors.BOLD}✨ 訂閱系統重構成功，核心功能正常運作 ✨{Colors.ENDC}\n"
            )
        else:
            print_failure("部分測試失敗")
            print(f"\n{Colors.FAIL}{Colors.BOLD}⚠️  請檢查失敗的測試項目 ⚠️{Colors.ENDC}\n")

        return result.returncode

    except Exception as e:
        print_failure(f"測試執行錯誤: {str(e)}")
        return 1


def generate_report():
    """生成測試報告"""
    print_section("📈 生成測試報告...")

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/e2e/test_subscription_integration_full.py",
        "--tb=short",
        "--junit-xml=tests/e2e/report.xml",
        "-v",
    ]

    subprocess.run(cmd, capture_output=True)
    print_success("測試報告已生成: tests/e2e/report.xml")


if __name__ == "__main__":
    exit_code = run_tests()

    if "--report" in sys.argv:
        generate_report()

    sys.exit(exit_code)
