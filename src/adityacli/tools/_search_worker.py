"""Isolated fallback regex worker. Called by SearchTool, never by model output."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

from adityacli.config import AppConfig, LMStudioConfig, SecurityConfig, WorkspaceConfig
from adityacli.core.workspace_guard import WorkspaceGuard
from adityacli.exceptions import InvalidPathError


def main() -> None:
    request = json.loads(sys.stdin.buffer.read(65536))
    cfg = AppConfig(WorkspaceConfig(Path(request["workspace"]), max_file_size=request["max_file_size"],
                                   encoding=request["encoding"]), LMStudioConfig(), SecurityConfig())
    query = request["query"]
    try:
        pattern = re.compile(re.escape(query) if request["literal"] else query,
                             0 if any(character.isupper() for character in query) else re.IGNORECASE)
    except re.error as exc:
        print(json.dumps({"error": f"Invalid search pattern: {exc}"}), flush=True)
        return
    guard = WorkspaceGuard(cfg)
    count = 0
    for path in guard.iter_files(max_size=True):
        relative = str(path.relative_to(guard.workspace))
        try:
            with guard.open_text(relative, cfg.workspace.encoding) as file:
                for number, line in enumerate(file, 1):
                    if "\x00" in line:
                        break
                    if pattern.search(line):
                        print(json.dumps({"match": f"{relative}:{number}:{line.rstrip()[:300]}"}), flush=True)
                        count += 1
                        if count >= 51:
                            return
        except (UnicodeError, OSError, InvalidPathError):
            continue


if __name__ == "__main__":
    main()
