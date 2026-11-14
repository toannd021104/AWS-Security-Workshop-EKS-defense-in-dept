#!/usr/bin/env python3
"""Check language coverage and preserve executable examples across editions."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
content = root / 'workshop/content'
errors = []
count = 0
blocks = 0

def code_blocks(text):
    return [(kind.strip(), code) for kind, code in re.findall(r'^```([^\n]*)\n(.*?)^```', text, flags=re.M | re.S)]

def normalized(code):
    return '\n'.join(line.rstrip() for line in code.splitlines() if line.strip() and not line.lstrip().startswith('#'))

for original in sorted(content.rglob('_index.md')):
    translated = original.with_name('_index.en.md')
    label = str(original.parent.relative_to(content))
    if not translated.exists():
        errors.append(f'{label}: missing English page')
        continue
    count += 1
    vi, en = original.read_text(), translated.read_text()
    for field in ['weight', 'sequenceSkip', 'previousLesson', 'nextLesson']:
        pattern = rf'(?m)^{field}:.*$'
        if re.findall(pattern, vi) != re.findall(pattern, en):
            errors.append(f'{label}: {field} differs')
    left, right = code_blocks(vi), code_blocks(en)
    if len(left) != len(right):
        errors.append(f'{label}: code block count differs')
    for index, (a, b) in enumerate(zip(left, right)):
        blocks += 1
        if a[0] != b[0] or normalized(a[1]) != normalized(b[1]):
            errors.append(f'{label}: example {index + 1} differs beyond comment translation')
    prose = re.sub(r'^```[^\n]*\n.*?^```', '', en, flags=re.M | re.S)
    if re.search(r'[ăâđêôơưĂÂĐÊÔƠƯ\u1ea0-\u1ef9]', prose):
        errors.append(f'{label}: Vietnamese text remains in English prose')
    if '{{CODE' in en:
        errors.append(f'{label}: unresolved code placeholder')
for translated in content.rglob('_index.en.md'):
    if not translated.with_name('_index.md').exists():
        errors.append(f'{translated}: missing Vietnamese counterpart')
print(f'{count} language pairs, {blocks} shared examples, {len(errors)} errors')
for error in errors:
    print(error)
sys.exit(bool(errors))
