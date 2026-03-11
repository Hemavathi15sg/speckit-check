#!/usr/bin/env python3
"""Count lines of code excluding comments, blank lines, and docstrings."""

import sys

def count_code_lines(filepath):
    """Count executable code lines."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total = len(lines)
    blank = sum(1 for line in lines if not line.strip())
    comments = sum(1 for line in lines if line.strip().startswith('#'))
    
    # Simple heuristic: count lines in triple-quoted strings as docstrings
    in_docstring = False
    docstring_lines = 0
    for line in lines:
        stripped = line.strip()
        if '"""' in stripped or "'''" in stripped:
            docstring_lines += 1
            if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                in_docstring = not in_docstring
        elif in_docstring:
            docstring_lines += 1
    
    code_lines = total - blank - comments - docstring_lines
    
    print(f"Total lines: {total}")
    print(f"Blank lines: {blank}")
    print(f"Comment lines: {comments}")
    print(f"Docstring lines: {docstring_lines}")
    print(f"Code lines: {code_lines}")
    
    return code_lines

if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'search/validation_module.py'
    count = count_code_lines(filepath)
    if count <= 300:
        print(f"\n✓ PASS: {count} ≤ 300 lines")
    else:
        print(f"\n✗ WARNING: {count} > 300 lines (target: ≤300)")
