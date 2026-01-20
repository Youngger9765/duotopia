#!/usr/bin/env python3
"""
Duotopia - Intelligent File Size Check Hook
Context-aware file size checking with POC/experimental code detection
Triggers: PreToolUse(Write|Edit)

Behavior:
- POC/Experimental files: Relaxed checks, suggestions only
- Production code: Strict enforcement
- User can override with special comment
"""
import json
import os
import re
import sys

# File size thresholds (in lines)
SOFT_WARNING_THRESHOLD = 500   # First warning - suggest refactoring
HARD_WARNING_THRESHOLD = 1000  # Strong warning - recommend refactoring
CRITICAL_THRESHOLD = 2000       # Absolute critical - warn even for POC
DOCUMENTATION_THRESHOLD = 800   # Documentation files

# POC/Experimental file patterns (relaxed rules)
POC_PATTERNS = [
    r'poc_',
    r'demo_',
    r'temp_',
    r'draft_',
    r'experiment',
    r'prototype',
    r'seed_data',
    r'fixtures',
    r'_temp',
    r'_draft',
]

# POC/Experimental directory patterns
POC_DIRECTORIES = [
    'poc',
    'pocs',
    'demo',
    'demos',
    'temp',
    'draft',
    'experiments',
    'prototypes',
    'scripts',
    'tools',
    'fixtures',
]

# Production code patterns (strict rules)
PRODUCTION_PATTERNS = [
    r'routers/',
    r'pages/',
    r'components/',
    r'services/',
    r'models/',
    r'controllers/',
    r'api/',
]

# Ignore check comment pattern
IGNORE_PATTERN = r'#\s*file-size-check:\s*ignore'

def count_file_lines(file_path):
    """Count number of lines in a file"""
    if not os.path.exists(file_path):
        return 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0

def has_ignore_comment(file_path):
    """Check if file has file-size-check: ignore comment"""
    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Check first 10 lines for ignore comment
            for i, line in enumerate(f):
                if i >= 10:
                    break
                if re.search(IGNORE_PATTERN, line):
                    return True
        return False
    except Exception:
        return False

def is_poc_or_experimental(file_path):
    """Detect if file is POC/experimental code (relaxed rules)"""
    file_name = os.path.basename(file_path)
    dir_path = os.path.dirname(file_path)

    # Check filename patterns
    for pattern in POC_PATTERNS:
        if re.search(pattern, file_name, re.IGNORECASE):
            return True

    # Check directory patterns
    path_parts = dir_path.split(os.sep)
    for part in path_parts:
        if part.lower() in POC_DIRECTORIES:
            return True

    # Check for test files (test_*.py or *.test.ts)
    if file_name.startswith('test_') or '.test.' in file_name or '.spec.' in file_name:
        return True

    return False

def is_production_code(file_path):
    """Detect if file is production code (strict rules)"""
    # Normalize path for pattern matching
    normalized_path = file_path.replace(os.sep, '/')

    for pattern in PRODUCTION_PATTERNS:
        if re.search(pattern, normalized_path):
            return True

    return False

def get_context_type(file_path):
    """Determine file context: 'production', 'poc', or 'general'"""
    if is_production_code(file_path):
        return 'production'
    elif is_poc_or_experimental(file_path):
        return 'poc'
    else:
        return 'general'

def is_documentation(file_path):
    """Check if file is documentation"""
    return file_path.endswith('.md')

def get_file_type(file_path):
    """Get file type for specific thresholds"""
    ext = os.path.splitext(file_path)[1]
    type_map = {
        '.py': 'Python',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript React',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript React',
        '.md': 'Documentation',
    }
    return type_map.get(ext, 'Unknown')

def get_severity_and_message(line_count, context_type, is_doc):
    """Determine severity level and appropriate message based on context"""

    # Documentation files have different threshold
    if is_doc:
        if line_count >= DOCUMENTATION_THRESHOLD:
            return 'warning', 'suggestion'
        return None, None

    # Handle different contexts
    if context_type == 'poc':
        # POC/Experimental: Very relaxed
        if line_count >= CRITICAL_THRESHOLD:
            # Even POC files shouldn't be this large (performance issues)
            return 'warning', 'performance'
        elif line_count >= HARD_WARNING_THRESHOLD:
            # Just a gentle suggestion
            return 'info', 'poc_suggestion'
        return None, None

    elif context_type == 'production':
        # Production: Strict enforcement
        if line_count >= HARD_WARNING_THRESHOLD:
            return 'critical', 'refactor_required'
        elif line_count >= SOFT_WARNING_THRESHOLD:
            return 'warning', 'refactor_recommended'
        return None, None

    else:
        # General: Moderate enforcement
        if line_count >= HARD_WARNING_THRESHOLD:
            return 'warning', 'refactor_recommended'
        elif line_count >= SOFT_WARNING_THRESHOLD:
            return 'info', 'suggestion'
        return None, None

def suggest_modularization(file_path, line_count, file_type):
    """Suggest modularization strategies based on file type"""

    if file_type in ['Python']:
        return f"""
Suggested modularization for {file_path} ({line_count} lines):

Python Backend Files:
  {os.path.dirname(file_path)}/{os.path.basename(file_path).replace('.py', '')}/
    __init__.py           # Main exports
    core.py               # Core business logic
    operations.py         # CRUD operations
    utils.py              # Helper functions
    validators.py         # Input validation
    models.py             # Data models (if applicable)
"""
    elif file_type in ['TypeScript React', 'JavaScript React']:
        return f"""
Suggested modularization for {file_path} ({line_count} lines):

React Component Files:
  {os.path.dirname(file_path)}/{os.path.basename(file_path).replace('.tsx', '').replace('.jsx', '')}/
    index.tsx             # Main component
    hooks.ts              # Custom hooks
    components.tsx        # Sub-components
    utils.ts              # Helper functions
    types.ts              # TypeScript types/interfaces
    styles.ts             # Styled components (if applicable)
"""
    else:
        return f"""
Suggested modularization for {file_path} ({line_count} lines):

General approach:
  - Split by responsibility/feature
  - Extract reusable utilities
  - Separate types/interfaces
  - Create smaller, focused modules
"""

def print_message(severity, message_type, file_path, line_count, file_type, context_type):
    """Print appropriate message based on severity and context"""

    context_label = {
        'production': '🏭 Production Code',
        'poc': '🧪 POC/Experimental',
        'general': '📦 General Code'
    }[context_type]

    if severity == 'critical':
        # Production code exceeding 1000 lines - must refactor
        print(f"""
🔴🔴🔴 CRITICAL: PRODUCTION FILE TOO LARGE 🔴🔴🔴
╔═══════════════════════════════════════════════════════════════════╗
║  {context_label:64s} ║
║  📂 File: {os.path.basename(file_path):56s} ║
║  📏 Size: {line_count:4d} lines (Production limit: {HARD_WARNING_THRESHOLD})                     ║
║  📋 Type: {file_type:58s} ║
╚═══════════════════════════════════════════════════════════════════╝

⚠️  REQUIRED ACTIONS BEFORE MODIFICATION:
   1. ANALYZE file structure and responsibilities
   2. CREATE modularization plan (see suggestion below)
   3. GET user approval for refactoring
   4. REFACTOR into smaller modules FIRST
   5. THEN make your intended changes

{suggest_modularization(file_path, line_count, file_type)}

📋 REFACTORING BENEFITS:
   ✓ Better maintainability and code review
   ✓ Easier testing and debugging
   ✓ Reduced merge conflicts
   ✓ Improved code reusability
   ✓ Faster IDE performance

⚠️  Production code MUST be refactored before major modifications!
""")

    elif severity == 'warning':
        if message_type == 'performance':
            # POC file > 2000 lines - performance concern
            print(f"""
⚠️  WARNING: File Extremely Large (Performance Concern)
╔═══════════════════════════════════════════════════════════════════╗
║  {context_label:64s} ║
║  📂 File: {os.path.basename(file_path):56s} ║
║  📏 Size: {line_count:4d} lines (Performance threshold: {CRITICAL_THRESHOLD})             ║
║  📋 Type: {file_type:58s} ║
╚═══════════════════════════════════════════════════════════════════╝

💡 NOTICE:
   While this is POC/experimental code, files over {CRITICAL_THRESHOLD} lines may cause:
   - Slow IDE performance
   - Long compilation/build times
   - Difficult code navigation

   Consider splitting even POC code for better development experience.
   You may continue, but be aware of potential performance impact.
""")
        elif message_type == 'refactor_recommended':
            # Production code 500-1000 lines OR general code > 1000 lines
            print(f"""
⚠️  WARNING: Large File - Refactoring Recommended
╔═══════════════════════════════════════════════════════════════════╗
║  {context_label:64s} ║
║  📂 File: {os.path.basename(file_path):56s} ║
║  📏 Size: {line_count:4d} lines (Warning at {SOFT_WARNING_THRESHOLD})                          ║
║  📋 Type: {file_type:58s} ║
╚═══════════════════════════════════════════════════════════════════╝

💡 RECOMMENDATION:
   - If adding significant code (>50 lines), consider refactoring FIRST
   - {'Production code should be kept modular for maintainability' if context_type == 'production' else 'Consider splitting into smaller modules'}
   - File is approaching critical threshold ({HARD_WARNING_THRESHOLD} lines for production)

You may proceed with small changes, but plan refactoring soon.
""")
        elif message_type == 'suggestion':
            # Documentation > 800 lines
            print(f"""
💡 SUGGESTION: Documentation File Getting Large
╔═══════════════════════════════════════════════════════════════════╗
║  📄 Documentation File                                            ║
║  📂 File: {os.path.basename(file_path):56s} ║
║  📏 Size: {line_count:4d} lines (Suggested limit: {DOCUMENTATION_THRESHOLD})                ║
╚═══════════════════════════════════════════════════════════════════╝

💡 Consider splitting into multiple topic-focused documents for easier navigation.
""")

    elif severity == 'info':
        if message_type == 'poc_suggestion':
            # POC file 1000-2000 lines
            print(f"""
💡 INFO: POC File Getting Large
╔═══════════════════════════════════════════════════════════════════╗
║  {context_label:64s} ║
║  📂 File: {os.path.basename(file_path):56s} ║
║  📏 Size: {line_count:4d} lines                                             ║
║  📋 Type: {file_type:58s} ║
╚═══════════════════════════════════════════════════════════════════╝

💡 SUGGESTION:
   This is experimental/POC code, so strict size limits don't apply.
   However, once validated and ready for production, consider refactoring
   into smaller modules for better maintainability.

   For now, you can continue without refactoring.
""")
        elif message_type == 'suggestion':
            # General code 500-1000 lines
            print(f"""
💡 INFO: File Size Notice
╔═══════════════════════════════════════════════════════════════════╗
║  {context_label:64s} ║
║  📂 File: {os.path.basename(file_path):56s} ║
║  📏 Size: {line_count:4d} lines                                             ║
║  📋 Type: {file_type:58s} ║
╚═══════════════════════════════════════════════════════════════════╝

💡 File is approaching size where refactoring becomes beneficial.
   Consider modularization when making major changes.
""")

def main():
    try:
        # Load input from stdin
        input_data = json.load(sys.stdin)

        # Get file path from tool parameters
        tool_params = input_data.get("tool_parameters", {})
        file_path = tool_params.get("file_path", "")

        if not file_path:
            # No file path, skip check
            sys.exit(0)

        # Check for ignore comment
        if has_ignore_comment(file_path):
            print(f"""
✅ File size check skipped for {os.path.basename(file_path)}
   Reason: User marked with '# file-size-check: ignore' comment
""")
            sys.exit(0)

        # Count lines in file
        line_count = count_file_lines(file_path)

        if line_count == 0:
            # File doesn't exist yet (new file) or empty, allow creation
            sys.exit(0)

        # Determine file context and type
        context_type = get_context_type(file_path)
        is_doc = is_documentation(file_path)
        file_type = get_file_type(file_path)

        # Get severity and message type
        severity, message_type = get_severity_and_message(line_count, context_type, is_doc)

        # Print appropriate message if any
        if severity:
            print_message(severity, message_type, file_path, line_count, file_type, context_type)

    except (json.JSONDecodeError, KeyError):
        # Invalid input, skip check
        pass
    except Exception as e:
        # Don't block on errors, just log
        print(f"⚠️  File size check warning: {str(e)}", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
