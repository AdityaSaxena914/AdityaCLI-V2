"""Query OSV for installed PyPI versions; never upload application sources."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from importlib.metadata import distributions
import json
from pathlib import Path
import platform
import re
from urllib.request import Request, urlopen


def query(endpoint: str, payload: dict) -> dict:
    request = Request(f"https://api.osv.dev/v1/{endpoint}",
                      data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json", "User-Agent": "AdityaCLI-dependency-audit"})
    with urlopen(request, timeout=30) as response:
        body = response.read(8 * 1024 * 1024 + 1)
    if len(body) > 8 * 1024 * 1024:
        raise RuntimeError("OSV response exceeded its limit; no clean result can be reported.")
    return json.loads(body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    packages = sorted({(re.sub(r"[-_.]+", "-", item.metadata["Name"]).lower(), item.version)
                       for item in distributions() if item.metadata["Name"].lower() != "adityacli"})
    queries = [{"package": {"name": name, "ecosystem": "PyPI"}, "version": version}
               for name, version in packages]
    results = []
    for offset in range(0, len(queries), 100):
        batch = queries[offset:offset + 100]
        page = query("querybatch", {"queries": batch})["results"]
        if len(page) != len(batch):
            raise RuntimeError("OSV returned an incomplete batch.")
        results.extend(page)
    matches = []
    for package, request, result in zip(packages, queries, results, strict=True):
        ids = {item["id"] for item in result.get("vulns", [])}
        while token := result.get("next_page_token"):
            result = query("query", {**request, "page_token": token})
            ids.update(item["id"] for item in result.get("vulns", []))
        if ids:
            matches.append({"name": package[0], "version": package[1], "advisory_ids": sorted(ids)})
    report = {"queried_at_utc": datetime.now(UTC).isoformat(), "source": "https://api.osv.dev/v1/querybatch",
              "python": platform.python_version(), "platform": platform.system(),
              "package_count": len(packages), "packages": [{"name": name, "version": version} for name, version in packages],
              "matched_packages": matches,
              "advisory_id_count": len({identifier for match in matches for identifier in match["advisory_ids"]}),
              "limitations": "Known version matches only; absence of matches does not establish absence of vulnerabilities."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Queried {len(packages)} installed packages; {len(matches)} matched packages.")
    return bool(matches)


if __name__ == "__main__":
    raise SystemExit(main())
