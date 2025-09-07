#!/usr/bin/env python3
"""
Pre-commit hook to check router prefix consistency
確保所有 router 都有正確的 prefix 設定
"""
import os
import re
import sys


def check_router_files():
    """檢查所有 router 檔案的 prefix 設定"""
    backend_routers = "backend/routers"
    errors = []

    # 預期的 router 設定規則
    expected_prefixes = {
        "auth.py": "/api/auth",
        "public.py": "/api/public",
        "students.py": "/api/students",
        "teachers.py": "/api/teachers",
        "assignments.py": "/api/teachers",  # 應該在 teachers 下
        "unassign.py": "/api/teachers",  # 應該在 teachers 下
    }

    for filename in os.listdir(backend_routers):
        if filename.endswith(".py") and filename != "__init__.py":
            filepath = os.path.join(backend_routers, filename)

            with open(filepath, "r") as f:
                content = f.read()

                # 尋找 router 定義
                router_pattern = r"router\s*=\s*APIRouter\((.*?)\)"
                matches = re.findall(router_pattern, content, re.DOTALL)

                if matches:
                    router_def = matches[0]

                    # 檢查是否有 prefix
                    prefix_pattern = r'prefix\s*=\s*["\']([^"\']+)["\']'
                    prefix_match = re.search(prefix_pattern, router_def)

                    if not prefix_match:
                        errors.append(f"❌ {filename}: 沒有設定 router prefix")
                    else:
                        actual_prefix = prefix_match.group(1)

                        # 檢查 prefix 是否符合預期
                        if filename in expected_prefixes:
                            expected = expected_prefixes[filename]
                            if actual_prefix != expected:
                                errors.append(
                                    f"❌ {filename}: prefix 錯誤\n" f"   預期: {expected}\n" f"   實際: {actual_prefix}"
                                )

                        # 檢查 prefix 格式
                        if not actual_prefix.startswith("/api/"):
                            errors.append(f"❌ {filename}: prefix 應該以 /api/ 開頭\n" f"   實際: {actual_prefix}")

    return errors


if __name__ == "__main__":
    print("🔍 檢查 Router Prefix 設定...")

    errors = check_router_files()

    if errors:
        print("\n發現問題：")
        for error in errors:
            print(error)
        sys.exit(1)
    else:
        print("✅ 所有 router prefix 設定正確！")
        sys.exit(0)
