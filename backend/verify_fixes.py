#!/usr/bin/env python3
"""
Verification script for Story 3.1 code review fixes.
Checks that all required changes were made.
"""

import os
import re

def check_file(filepath, checks):
    """Check a file for required patterns."""
    print(f"\n📄 Checking {filepath}")
    
    if not os.path.exists(filepath):
        print(f"  ❌ File not found!")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    all_passed = True
    for check_name, pattern, should_exist in checks:
        found = bool(re.search(pattern, content, re.MULTILINE | re.DOTALL))
        
        if should_exist and found:
            print(f"  ✅ {check_name}")
        elif not should_exist and not found:
            print(f"  ✅ {check_name} (correctly absent)")
        else:
            print(f"  ❌ {check_name} - {'MISSING' if should_exist else 'SHOULD BE REMOVED'}")
            all_passed = False
    
    return all_passed

# Check base.py
base_checks = [
    ("No SpoonReactMCP inheritance", r"class BaseDesignerAgent\(SpoonReactMCP", False),
    ("ABC inheritance", r"class BaseDesignerAgent\(ABC\)", True),
    ("ValueError in _format_amount", r"raise ValueError.*amount or percentage", True),
    ("Proper error documentation", r"Raises:\s+ValueError", True),
]

# Check __init__.py
init_checks = [
    ("NODE_X_POSITION constant", r"NODE_X_POSITION\s*=\s*250", True),
    ("NODE_Y_SPACING constant", r"NODE_Y_SPACING\s*=\s*150", True),
    ("Pre-instantiated designers", r"trigger_designer = create_trigger_designer\(\)", True),
    ("Specific exceptions", r"except \(ValidationError, ValueError, AttributeError\)", True),
    ("ValidationError import", r"from pydantic import ValidationError", True),
]

# Check trigger_designer.py
trigger_checks = [
    ("No system prompt", r"TRIGGER_DESIGNER_SYSTEM_PROMPT", False),
    ("No _refresh_prompts", r"def _refresh_prompts", False),
    ("Factory returns no llm", r"return TriggerDesignerAgent\(\)", True),
]

# Check transfer_designer.py
transfer_checks = [
    ("No system prompt", r"TRANSFER_DESIGNER_SYSTEM_PROMPT", False),
    ("Address documentation", r"Neo N3 addresses are 34 characters", True),
    ("Address format example", r'Example:.*→.*\.\.\.', True),
]

# Check test_designers.py
test_checks = [
    ("No timing test", r"test_parallel_execution_speed", False),
    ("Gather verification test", r"test_parallel_execution_uses_gather", True),
    ("Monkeypatch usage", r"monkeypatch", True),
]

print("=" * 60)
print("Story 3.1 Code Review Fixes - Verification")
print("=" * 60)

results = []
results.append(check_file("app/agents/designers/base.py", base_checks))
results.append(check_file("app/agents/designers/__init__.py", init_checks))
results.append(check_file("app/agents/designers/trigger_designer.py", trigger_checks))
results.append(check_file("app/agents/designers/transfer_designer.py", transfer_checks))
results.append(check_file("tests/test_designers.py", test_checks))

print("\n" + "=" * 60)
if all(results):
    print("✅ ALL FIXES VERIFIED - READY FOR PRODUCTION")
else:
    print("❌ SOME FIXES MISSING - REVIEW REQUIRED")
print("=" * 60)
