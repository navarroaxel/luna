#!/usr/bin/env python3
"""Build go2rtc.yaml from cameras.json + .env."""
import json
from pathlib import Path
from urllib.parse import urlencode

root = Path(__file__).parent
env = {}
for line in (root / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k] = v

missing = [k for k in ("NEST_PROJECT_ID", "NEST_CLIENT_ID", "NEST_CLIENT_SECRET", "NEST_REFRESH_TOKEN") if not env.get(k)]
if missing:
    raise SystemExit(f"Missing in .env: {', '.join(missing)}")

cameras = json.loads((root / "cameras.json").read_text())
lines = ["streams:"]
for cam in cameras:
    if cam["device_id"] == "REPLACE_ME":
        raise SystemExit(f"Set device_id for {cam['id']} in cameras.json")
    q = urlencode({
        "client_id": env["NEST_CLIENT_ID"],
        "client_secret": env["NEST_CLIENT_SECRET"],
        "refresh_token": env["NEST_REFRESH_TOKEN"],
        "project_id": env["NEST_PROJECT_ID"],
        "device_id": cam["device_id"],
    })
    lines.append(f"  {cam['id']}: nest:?{q}")

lines += [
    "",
    "api:",
    '  listen: ":1984"',
    "  static_dir: /www",
    "",
    "webrtc:",
    '  listen: ":8555"',
    "",
]
(root / "go2rtc.yaml").write_text("\n".join(lines))
print(f"Wrote go2rtc.yaml with {len(cameras)} streams")
