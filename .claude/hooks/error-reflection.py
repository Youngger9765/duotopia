#!/usr/bin/env python3
"""
Error Reflection Hook
Automatically detects errors in Claude's output and triggers learning reflection.
Hook: UserPromptEnd
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
HOOK_DIR = Path(__file__).parent
PROJECT_ROOT = HOOK_DIR.parent.parent
LEARNING_DIR = HOOK_DIR.parent / "learning"
AGENTS_DIR = HOOK_DIR.parent / "agents"

# Error detection patterns
ERROR_PATTERNS = {
    "test_failure": {
        "keywords": ["test failed", "assertion error", "test failure", "tests failed", "pytest failed"],
        "severity": "high",
        "category": "testing"
    },
    "build_failure": {
        "keywords": ["build failed", "compilation error", "build error", "npm run build failed"],
        "severity": "high",
        "category": "build"
    },
    "runtime_error": {
        "keywords": ["exception", "error:", "traceback", "fatal", "crash"],
        "severity": "high",
        "category": "runtime"
    },
    "workflow_violation": {
        "keywords": [
            "without running tests",
            "without verification",
            "skip test",
            "hasty judgment",
            "premature completion",
            "forgot to test",
            "didn't test"
        ],
        "severity": "critical",
        "category": "workflow"
    },
    "security_issue": {
        "keywords": [
            "security vulnerability",
            "exposed secret",
            "hardcoded password",
            "sql injection",
            "xss vulnerability"
        ],
        "severity": "critical",
        "category": "security"
    },
    "integration_failure": {
        "keywords": [
            "api error",
            "connection refused",
            "timeout",
            "database error",
            "network error"
        ],
        "severity": "medium",
        "category": "integration"
    },
    "logic_error": {
        "keywords": [
            "wrong result",
            "incorrect output",
            "logic error",
            "off by one",
            "wrong calculation"
        ],
        "severity": "medium",
        "category": "logic"
    },
    "user_correction": {
        "keywords": [
            "actually",
            "that's wrong",
            "incorrect",
            "you made a mistake",
            "this doesn't work"
        ],
        "severity": "high",
        "category": "accuracy"
    }
}

# Severity levels
SEVERITY_LEVELS = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1
}


def ensure_learning_files():
    """Ensure all learning files exist with proper structure."""
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)

    files = {
        "error-patterns.json": {
            "patterns": [],
            "statistics": {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
        },
        "improvements.json": {
            "improvements": []
        },
        "user-preferences.json": {
            "preferences": {
                "communication_style": "concise",
                "detail_level": "high",
                "auto_fix": False,
                "notification_threshold": "medium",
                "learning_mode": "active"
            },
            "workflows": {
                "preferred_test_runner": "pytest",
                "git_workflow": "feature-branch",
                "commit_style": "conventional",
                "deployment_approval": "manual"
            },
            "quality_standards": {
                "min_test_coverage": 80,
                "required_checks": ["tests", "typecheck", "lint"],
                "security_scan": True,
                "performance_benchmark": True
            }
        },
        "performance-metrics.json": {
            "metrics": {
                "error_rate": {
                    "current_week": 0.0,
                    "last_week": 0.0,
                    "trend": "stable",
                    "target": 0.02
                },
                "repeat_errors": {
                    "current_week": 0,
                    "last_week": 0,
                    "trend": "stable",
                    "target": 0
                },
                "time_to_fix": {
                    "average_minutes": 0,
                    "median_minutes": 0,
                    "trend": "stable"
                },
                "test_coverage": {
                    "current": 0,
                    "target": 90,
                    "trend": "stable"
                }
            },
            "weekly_summary": {
                "week_of": datetime.now().strftime("%Y-%m-%d"),
                "total_tasks": 0,
                "errors_caught": 0,
                "errors_prevented": 0,
                "top_improvement": "System initialized"
            }
        }
    }

    for filename, default_content in files.items():
        filepath = LEARNING_DIR / filename
        if not filepath.exists():
            with open(filepath, 'w') as f:
                json.dump(default_content, f, indent=2)


def load_json(filename: str) -> Dict:
    """Load JSON file from learning directory."""
    filepath = LEARNING_DIR / filename
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(filename: str, data: Dict):
    """Save JSON file to learning directory."""
    filepath = LEARNING_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def detect_errors(text: str) -> List[Dict]:
    """Detect errors in the given text."""
    errors = []
    text_lower = text.lower()

    for error_type, config in ERROR_PATTERNS.items():
        for keyword in config["keywords"]:
            if keyword.lower() in text_lower:
                errors.append({
                    "type": error_type,
                    "keyword": keyword,
                    "severity": config["severity"],
                    "category": config["category"],
                    "timestamp": datetime.now().isoformat()
                })
                break  # Only record once per error type

    return errors


def find_or_create_pattern(error: Dict, patterns_data: Dict) -> Optional[str]:
    """Find existing pattern or create new one."""
    patterns = patterns_data.get("patterns", [])

    # Try to find existing pattern
    for pattern in patterns:
        if (pattern["category"] == error["category"] and
            pattern["severity"] == error["severity"] and
            error["type"] in pattern.get("error_types", [])):
            return pattern["id"]

    # Create new pattern
    new_id = f"P{len(patterns) + 1:03d}"
    new_pattern = {
        "id": new_id,
        "category": error["category"],
        "severity": error["severity"],
        "error_types": [error["type"]],
        "description": f"{error['category'].title()} error: {error['type']}",
        "occurrences": 0,
        "last_seen": error["timestamp"],
        "root_causes": [],
        "prevention_strategies": [],
        "related_patterns": []
    }
    patterns.append(new_pattern)
    patterns_data["patterns"] = patterns

    return new_id


def update_patterns(errors: List[Dict]):
    """Update error patterns database."""
    if not errors:
        return

    patterns_data = load_json("error-patterns.json")

    for error in errors:
        pattern_id = find_or_create_pattern(error, patterns_data)

        # Update pattern occurrence
        for pattern in patterns_data["patterns"]:
            if pattern["id"] == pattern_id:
                pattern["occurrences"] += 1
                pattern["last_seen"] = error["timestamp"]
                break

        # Update statistics
        stats = patterns_data.setdefault("statistics", {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0}
        })

        stats["total_errors"] += 1
        stats["by_category"][error["category"]] = stats["by_category"].get(error["category"], 0) + 1
        stats["by_severity"][error["severity"]] += 1

    save_json("error-patterns.json", patterns_data)


def update_metrics(errors: List[Dict]):
    """Update performance metrics."""
    if not errors:
        return

    metrics_data = load_json("performance-metrics.json")

    # Update error counts
    metrics = metrics_data.setdefault("metrics", {})

    # Update current week stats
    error_rate = metrics.setdefault("error_rate", {})
    error_rate["current_week"] = error_rate.get("current_week", 0.0) + len(errors) * 0.01

    repeat_errors = metrics.setdefault("repeat_errors", {})
    # Check if any errors are repeats
    patterns_data = load_json("error-patterns.json")
    for error in errors:
        for pattern in patterns_data.get("patterns", []):
            if (error["category"] == pattern["category"] and
                pattern["occurrences"] > 1):
                repeat_errors["current_week"] = repeat_errors.get("current_week", 0) + 1
                break

    # Update weekly summary
    weekly = metrics_data.setdefault("weekly_summary", {})
    weekly["errors_caught"] = weekly.get("errors_caught", 0) + len(errors)

    save_json("performance-metrics.json", metrics_data)


def generate_reflection_prompt(errors: List[Dict]) -> str:
    """Generate reflection prompt for Claude."""
    if not errors:
        return ""

    # Get highest severity error
    sorted_errors = sorted(errors, key=lambda e: SEVERITY_LEVELS.get(e["severity"], 0), reverse=True)
    primary_error = sorted_errors[0]

    patterns_data = load_json("error-patterns.json")

    # Find related pattern
    pattern_info = ""
    for pattern in patterns_data.get("patterns", []):
        if (pattern["category"] == primary_error["category"] and
            pattern["severity"] == primary_error["severity"]):
            pattern_info = f"""
**Pattern History**: Pattern {pattern['id']} - {pattern['occurrences']} occurrences
**Last Seen**: {pattern['last_seen']}
"""
            if pattern.get("prevention_strategies"):
                pattern_info += f"**Known Prevention Strategies**:\n"
                for strategy in pattern["prevention_strategies"]:
                    pattern_info += f"- {strategy}\n"
            break

    prompt = f"""
🔍 **Error Detection Alert**

**Severity**: {primary_error['severity'].upper()}
**Category**: {primary_error['category'].title()}
**Type**: {primary_error['type']}
**Detected**: {primary_error['timestamp']}
{pattern_info}

**Required Actions**:
1. Acknowledge the error
2. Analyze root cause
3. Implement immediate fix
4. Update prevention strategies
5. Verify fix with tests

⚠️ Please reflect on this error and update your approach to prevent recurrence.
"""

    return prompt


def main():
    """Main hook execution."""
    try:
        # Ensure learning files exist
        ensure_learning_files()

        # Read input from stdin
        input_data = sys.stdin.read()

        # Try to parse as JSON
        try:
            data = json.loads(input_data)
            text = data.get("output", "") + " " + data.get("prompt", "")
        except json.JSONDecodeError:
            text = input_data

        # Detect errors
        errors = detect_errors(text)

        if errors:
            # Update patterns and metrics
            update_patterns(errors)
            update_metrics(errors)

            # Generate reflection prompt
            reflection = generate_reflection_prompt(errors)

            # Output for Claude
            print(reflection)

    except Exception as e:
        # Silent fail - don't break Claude's flow
        # Log to error file for debugging
        error_log = LEARNING_DIR / "hook-errors.log"
        with open(error_log, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {str(e)}\n")


if __name__ == "__main__":
    main()
