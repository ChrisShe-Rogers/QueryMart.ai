import base64
import json
from typing import Any

from fastapi import HTTPException


def encode_cursor(data: dict[str, Any]) -> str:
    payload = json.dumps(data, separators=(",", ":"), sort_keys=True)
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> dict[str, Any]:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(f"{cursor}{padding}".encode()).decode()
        data = json.loads(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid cursor")
    return data
