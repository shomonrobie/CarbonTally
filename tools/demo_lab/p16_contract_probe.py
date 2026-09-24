"""P16 helper — dump the real OpenAPI contract slices needed for the journey driver.

Read-only utility. Prints the exact route + request schema for the routes the
P16 core-accounting journey must call, so the driver uses the real contract
instead of invented request shapes.
"""
from __future__ import annotations

import json
import re
import sys

SPEC = "/tmp/p16_openapi.json"
PATTERNS = sys.argv[1:] or [
    r"supplier",
    r"^/api/v3/processing/",
    r"^/api/v3/reports",
    r"^/api/v3/documents",
    r"upload",
    r"^/api/v3/emissions",
    r"^/api/v3/evidence",
]


def main() -> int:
    spec = json.load(open(SPEC))
    paths = spec["paths"]
    schemas = spec.get("components", {}).get("schemas", {})

    def deref(node):
        if isinstance(node, dict) and "$ref" in node:
            return schemas.get(node["$ref"].split("/")[-1], {})
        return node

    rx = re.compile("|".join(PATTERNS), re.I)
    selected = sorted(k for k in paths if rx.search(k))
    print(f"SELECTED ROUTES: {len(selected)}\n")
    for path in selected:
        for method in ("post", "put", "patch", "get"):
            op = paths[path].get(method)
            if not op:
                continue
            line = f"{method.upper():6} {path}"
            params = [
                p.get("name")
                for p in (op.get("parameters") or [])
                if p.get("in") in ("query", "path")
            ]
            if params:
                line += f"   [params: {', '.join(params)}]"
            print(line)
            body = op.get("requestBody")
            if body:
                for ctype, spec_body in (body.get("content") or {}).items():
                    node = deref(spec_body.get("schema", {}))
                    props = node.get("properties") or {}
                    if not props:
                        print(f"        body({ctype}): {str(node)[:80]}")
                        continue
                    req = set(node.get("required") or [])
                    print(f"        body({ctype}) required={sorted(req)}")
                    for name, spec_prop in list(props.items())[:24]:
                        kind = spec_prop.get("type") or spec_prop.get("anyOf") or "?"
                        print(f"          - {name}: {str(kind)[:64]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
