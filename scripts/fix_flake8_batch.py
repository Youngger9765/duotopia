#!/usr/bin/env python3
"""批量修復 flake8 錯誤"""

import os
import re
import glob

def fix_f_string_missing_placeholders(content):
    """修復沒有佔位符的 f-string (F541)"""
    # 尋找 f"..." 或 f'...' 沒有 {} 的情況
    content = re.sub(r'f"([^{}]*?)"', r'"\1"', content)
    content = re.sub(r"f'([^{}]*?)'", r"'\1'", content)
    return content

def fix_unused_imports(filepath):
    """修復未使用的 imports (F401)"""
    unused_imports = {
        'backend/routers/unassign.py': ['sqlalchemy.and_'],
        'backend/schemas.py': ['pydantic.validator'],
        'backend/services/audio_upload.py': ['tempfile'],
        'backend/tests/e2e/test_assignments_flow.py': ['json'],
        'backend/tests/e2e/test_complete_assignment_flow.py': ['json'],
        'backend/tests/e2e/test_real_api.py': ['json'],
        'backend/tests/integration/api/test_assign_student.py': ['json'],
        'backend/tests/integration/api/test_assignment_complete.py': ['json'],
        'backend/tests/integration/api/test_assignment_detail.py': ['json'],
    }

    filename = filepath.replace('/Users/young/project/duotopia/', '')
    if filename in unused_imports:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            should_remove = False
            for unused in unused_imports[filename]:
                if f'import {unused}' in line or f'from {unused}' in line:
                    should_remove = True
                    break
            if not should_remove:
                new_lines.append(line)

        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        return True
    return False

def fix_file(filepath):
    """修復單一檔案的 flake8 錯誤"""
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # 修復 f-string 沒有佔位符
    content = fix_f_string_missing_placeholders(content)

    # 修復 E712: comparison to True/False
    content = re.sub(r'(\w+)\s*==\s*True\b', r'\1 is True', content)
    content = re.sub(r'(\w+)\s*==\s*False\b', r'\1 is False', content)

    # 修復 E711: comparison to None
    content = re.sub(r'(\w+)\s*==\s*None\b', r'\1 is None', content)
    content = re.sub(r'(\w+)\s*!=\s*None\b', r'\1 is not None', content)

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True

    # 嘗試修復未使用的 imports
    if fix_unused_imports(filepath):
        print(f"Fixed imports: {filepath}")
        return True

    return False

def main():
    """修復所有 Python 檔案"""
    fixed_count = 0

    # 修復後端檔案
    backend_patterns = [
        'backend/**/*.py',
        'backend/*.py'
    ]

    for pattern in backend_patterns:
        for filepath in glob.glob(pattern, recursive=True):
            if fix_file(filepath):
                fixed_count += 1

    print(f"\n總共修復 {fixed_count} 個檔案")

if __name__ == '__main__':
    main()
