from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request


def parse_payload(raw: str) -> bytes:
    try:
        return json.dumps(json.loads(raw), ensure_ascii=False).encode("utf-8")
    except json.JSONDecodeError:
        repaired = raw.strip()
        repaired = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)", r'\1"\2"\3', repaired)
        repaired = re.sub(r":\s*([A-Za-z_][A-Za-z0-9_-]*)(\s*[,}])", r':"\1"\2', repaired)
        repaired = repaired.replace(':"true"', ":true").replace(':"false"', ":false").replace(':"null"', ":null")
        return json.dumps(json.loads(repaired), ensure_ascii=False).encode("utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python client.py \'{"action":"health"}\'', file=sys.stderr)
        return 2

    try:
        payload = parse_payload(sys.argv[1])
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON payload: {exc}", file=sys.stderr)
        print("PowerShell example: python client.py '{\"action\":\"health\"}'", file=sys.stderr)
        return 2

    bridge_url = os.getenv("AUTOCAD_BRIDGE_URL", "http://127.0.0.1:8766/execute")
    request = urllib.request.Request(
        bridge_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}: {exc.reason}", file=sys.stderr)
        try:
            print(json.dumps(json.loads(body), ensure_ascii=False, indent=2), file=sys.stderr)
        except json.JSONDecodeError:
            print(body, file=sys.stderr)
        return 1
    print(json.dumps(json.loads(body), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

