from pathlib import Path
from collections import defaultdict
import json

MIN_OVERLAP_LINE_LENGTH = 20
target_dir = Path("boilerplate-agent")
md_files = list(target_dir.rglob("*.md"))
line_map = defaultdict(list)

for f in md_files:
    try:
        content = f.read_text()
        lines = [l.strip() for l in content.splitlines() if len(l.strip()) > MIN_OVERLAP_LINE_LENGTH]
        for l in set(lines): # using set to avoid same file counted multiple times for same line
            line_map[l].append(str(f))
    except Exception as e:
        pass

overlaps = {l: files for l, files in line_map.items() if len(files) > 1}
# sort by number of files
overlaps_sorted = dict(sorted(overlaps.items(), key=lambda item: len(item[1]), reverse=True))

print("Top 10 overlaps:")
for k, v in list(overlaps_sorted.items())[:10]:
    print(f"[{len(v)} files] {k[:60]}...")

