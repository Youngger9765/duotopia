#!/usr/bin/env python3
"""
Pre-commit hook to check Alembic migration file format
確保 migration 檔案符合標準格式，避免部署失敗
"""
import sys
import re
from pathlib import Path


def check_migration_file(filepath: str) -> tuple[bool, list[str]]:
    """
    檢查 migration 檔案格式
    Returns: (is_valid, error_messages)
    """
    errors = []
    path = Path(filepath)
    filename = path.name

    # 1. 檢查檔名格式: YYYYMMDD_HHMM_[12位hex]_description.py
    pattern = r"^\d{8}_\d{4}_[a-f0-9]{12}_[\w_]+\.py$"
    if not re.match(pattern, filename):
        errors.append(f"❌ 檔名格式錯誤: {filename}")
        errors.append("   正確格式: YYYYMMDD_HHMM_[12位hex]_description.py")
        errors.append("   範例: 20250901_0116_87293915d363_add_is_active.py")

    # 2. 檢查檔案內容
    try:
        with open(filepath, "r") as f:
            content = f.read()

        # 檢查 revision ID 格式（必須是12位 hex）
        revision_match = re.search(r"revision:\s*str\s*=\s*['\"]([^'\"]+)['\"]", content)
        if revision_match:
            revision = revision_match.group(1)
            if not re.match(r"^[a-f0-9]{12}$", revision):
                errors.append(f"❌ Revision ID 格式錯誤: '{revision}'")
                errors.append("   必須是12位十六進制字串")
                errors.append("   使用 alembic revision --autogenerate 自動生成")
        else:
            errors.append("❌ 找不到 revision 定義")

        # 檢查 down_revision
        down_revision_match = re.search(
            r"down_revision:\s*.*\s*=\s*['\"]([^'\"]*)['\"]|down_revision:\s*.*\s*=\s*None",
            content,
        )
        if down_revision_match and down_revision_match.group(1):
            down_revision = down_revision_match.group(1)
            # down_revision 應該是 12位 hex 或 None
            if down_revision and not re.match(r"^[a-f0-9]{12}$", down_revision):
                errors.append(f"❌ down_revision 格式錯誤: '{down_revision}'")
                errors.append("   必須是12位十六進制字串或 None")

        # 檢查是否包含 upgrade 和 downgrade 函數
        if "def upgrade()" not in content:
            errors.append("❌ 缺少 upgrade() 函數")
        if "def downgrade()" not in content:
            errors.append("❌ 缺少 downgrade() 函數")

        # 警告：檢查 upgrade() 函數中是否有危險操作（downgrade 中的 drop 是正常的）
        # 找出 upgrade 函數的內容
        upgrade_match = re.search(r"def upgrade\(\)[^:]*:(.*?)(?=def downgrade|$)", content, re.DOTALL)
        if upgrade_match:
            upgrade_content = upgrade_match.group(1)

            dangerous_patterns = [
                (
                    r"drop_table\(",
                    "⚠️  警告: upgrade() 中包含 drop_table - 請確認是否真的要刪除表",
                ),
                (
                    r"drop_column\(",
                    "⚠️  警告: upgrade() 中包含 drop_column - 請確認是否真的要刪除欄位",
                ),
                (
                    r"execute\(.*DELETE",
                    "⚠️  警告: upgrade() 中包含 DELETE 語句 - 請確認是否真的要刪除資料",
                ),
                (
                    r"execute\(.*TRUNCATE",
                    "⚠️  警告: upgrade() 中包含 TRUNCATE 語句 - 請確認是否真的要清空表",
                ),
            ]

            for pattern, message in dangerous_patterns:
                if re.search(pattern, upgrade_content, re.IGNORECASE):
                    # 這是警告不是錯誤，所以仍然返回 True
                    print(f"   {message}")

    except Exception as e:
        errors.append(f"❌ 無法讀取檔案: {e}")

    return (len(errors) == 0, errors)


def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("Usage: check_migration_format.py <migration_file> [migration_file2 ...]")
        sys.exit(1)

    all_valid = True

    for filepath in sys.argv[1:]:
        print(f"\n🔍 檢查: {filepath}")
        is_valid, errors = check_migration_file(filepath)

        if is_valid:
            print("   ✅ 格式正確")
        else:
            all_valid = False
            for error in errors:
                print(error)

    if not all_valid:
        print("\n❌ Migration 檔案格式檢查失敗！")
        print("\n建議:")
        print("1. 使用 alembic revision --autogenerate 生成 migration")
        print("2. 不要手動修改 revision ID")
        print("3. 檔名格式: YYYYMMDD_HHMM_[revision]_description.py")
        sys.exit(1)

    print("\n✅ 所有 migration 檔案格式正確")


if __name__ == "__main__":
    main()
