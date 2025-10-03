#!/usr/bin/env python3
"""
Pre-commit hook to check for problematic import patterns in Python files.
Prevents local imports that could shadow global imports and cause UnboundLocalError.
"""
import ast
import sys
import re
from pathlib import Path
from typing import List, Tuple


class ImportPatternChecker(ast.NodeVisitor):
    """AST visitor to check for problematic import patterns."""

    def __init__(self, filename: str):
        self.filename = filename
        self.errors: List[Tuple[int, str]] = []
        self.global_imports = set()
        self.current_function = None

    def visit_Module(self, node):
        """First pass: collect all top-level imports."""
        for item in ast.iter_child_nodes(node):
            if isinstance(item, (ast.Import, ast.ImportFrom)):
                if isinstance(item, ast.ImportFrom) and item.module:
                    self.global_imports.add(item.module)
                elif isinstance(item, ast.Import):
                    for alias in item.names:
                        self.global_imports.add(alias.name.split(".")[0])

        # Second pass: check for problematic patterns
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Check function definitions for local imports."""
        self.current_function = node.name
        self.check_function_body(node)
        self.generic_visit(node)
        self.current_function = None

    def visit_AsyncFunctionDef(self, node):
        """Check async function definitions for local imports."""
        self.current_function = node.name
        self.check_function_body(node)
        self.generic_visit(node)
        self.current_function = None

    def check_function_body(self, node):
        """Check for imports inside function bodies."""
        for item in ast.walk(node):
            if isinstance(item, (ast.Import, ast.ImportFrom)):
                # Check if this is a local import that could shadow global imports
                if isinstance(item, ast.ImportFrom):
                    if item.module and item.module in self.global_imports:
                        self.errors.append(
                            (
                                item.lineno,
                                f"Local import 'from {item.module} import ...' in function '{self.current_function}' "
                                f"shadows global import and could cause UnboundLocalError",
                            )
                        )

                    # Check for relative imports from models
                    if item.module == "models":
                        imported_names = [alias.name for alias in item.names]
                        self.errors.append(
                            (
                                item.lineno,
                                f"Local import 'from models import {', '.join(imported_names)}' in function "
                                f"'{self.current_function}' should be at module level to avoid UnboundLocalError",
                            )
                        )

                elif isinstance(item, ast.Import):
                    for alias in item.names:
                        module_name = alias.name.split(".")[0]
                        if module_name in self.global_imports:
                            self.errors.append(
                                (
                                    item.lineno,
                                    f"Local import '{alias.name}' in function '{self.current_function}' "
                                    f"shadows global import and could cause UnboundLocalError",
                                )
                            )


def check_file(filepath: Path) -> List[Tuple[int, str]]:
    """Check a single Python file for import issues."""
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))

        checker = ImportPatternChecker(str(filepath))
        checker.visit(tree)

        return checker.errors
    except SyntaxError as e:
        return [(e.lineno or 0, f"Syntax error: {e.msg}")]
    except Exception as e:
        return [(0, f"Error parsing file: {str(e)}")]


def check_common_patterns(filepath: Path) -> List[Tuple[int, str]]:
    """Check for common problematic patterns using regex."""
    errors = []
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Pattern 1: Check for 'from models import' inside functions
    in_function = False
    function_name = ""

    for i, line in enumerate(lines, 1):
        # Detect function definition
        if re.match(r"^(async\s+)?def\s+\w+\s*\(", line.strip()):
            in_function = True
            len(line) - len(line.lstrip())
            match = re.search(r"def\s+(\w+)", line)
            function_name = match.group(1) if match else "unknown"
            continue

        # Check if we're out of the function
        if in_function and line.strip() and not line[0].isspace():
            in_function = False
            function_name = ""

        # Check for problematic imports inside functions
        if in_function and "from models import" in line:
            errors.append(
                (
                    i,
                    f"Import 'from models import ...' inside function '{function_name}' "
                    f"should be moved to module level",
                )
            )

        # Check for StudentContentProgress import anywhere
        if "StudentContentProgress" in line and "import" in line:
            errors.append(
                (
                    i,
                    "Warning: StudentContentProgress import detected - verify if this model is still needed",
                )
            )

    return errors


def main():
    """Main entry point for the pre-commit hook."""
    if len(sys.argv) < 2:
        print("Usage: check_import_patterns.py <file1> [<file2> ...]")
        sys.exit(1)

    has_errors = False

    for filepath_str in sys.argv[1:]:
        filepath = Path(filepath_str)

        # Skip non-Python files
        if not filepath.suffix == ".py":
            continue

        # Skip test files, migration files, and hook scripts
        if (
            "test_" in filepath.name
            or "/alembic/versions/" in str(filepath)
            or "/hooks/" in str(filepath)
        ):
            continue

        print(f"Checking {filepath}...")

        # AST-based checks
        ast_errors = check_file(filepath)

        # Pattern-based checks
        pattern_errors = check_common_patterns(filepath)

        all_errors = ast_errors + pattern_errors

        if all_errors:
            has_errors = True
            print(f"\n❌ {filepath}:")
            for lineno, error in sorted(all_errors):
                if lineno > 0:
                    print(f"  Line {lineno}: {error}")
                else:
                    print(f"  {error}")
            print()

    if has_errors:
        print("\n⚠️  Import pattern issues detected!")
        print("📝 Fix suggestions:")
        print("  1. Move all 'from models import ...' statements to the module level")
        print("  2. Avoid importing inside functions unless absolutely necessary")
        print("  3. If lazy imports are needed, use full module paths")
        print("  4. Consider removing deprecated models like StudentContentProgress")
        sys.exit(1)
    else:
        print("✅ All import patterns look good!")
        sys.exit(0)


if __name__ == "__main__":
    main()
