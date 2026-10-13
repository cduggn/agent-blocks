"""Check relative Markdown file links under the supplied directory."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


root = Path(sys.argv[1])
files = list(root.rglob("*.md"))
if not files:
    sys.exit(f"No Markdown files found under {root}")
errors = []
for path in files:
    for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
        target = target.strip("<>")
        if urlsplit(target).scheme or target.startswith("#"):
            continue
        target = unquote(target.split("#", 1)[0])
        if not (path.parent / target).exists():
            errors.append(f"{path}: missing {target}")
if errors:
    sys.exit("\n".join(errors))
print(f"Relative file links resolve in {len(files)} Markdown files; external URLs and anchors not checked.")
