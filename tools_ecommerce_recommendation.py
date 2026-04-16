from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List


def _stable_ratio(*parts: str) -> float:
    payload = "|".join(parts).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:8]
    return int(digest, 16) / 0xFFFFFFFF


def _stable_int(low: int, high: int, *parts: str) -> int:
    ratio = _stable_ratio(*parts)
    return low + int((high - low) * ratio)


def _stable_score(*parts: str) -> str:
    score = 0.82 + (_stable_ratio(*parts) * 0.16)
    return f"{score:.3f}"


def generate_batch_snapshot(batch_date: str | None = None, model_version: str = "demo-v1") -> Dict[str, Any]:
    resolved_batch_date = batch_date or datetime.now().strftime("%Y-%m-%d")
    users_covered = _stable_int(1180000, 1340000, resolved_batch_date, model_version, "users")
    items_ranked = _stable_int(18000000, 26000000, resolved_batch_date, model_version, "items")

    preview: List[Dict[str, str]] = [
        {
            "user_id": "user_0001",
            "slot": "hero_banner",
            "item_id": "SKU-1452",
            "score": _stable_score(resolved_batch_date, model_version, "1"),
            "reason": "Recent clicks and cart intent",
        },
        {
            "user_id": "user_0002",
            "slot": "homepage_feed",
            "item_id": "SKU-2208",
            "score": _stable_score(resolved_batch_date, model_version, "2"),
            "reason": "Repeat-purchase pattern",
        },
        {
            "user_id": "user_0003",
            "slot": "homepage_feed",
            "item_id": "SKU-0871",
            "score": _stable_score(resolved_batch_date, model_version, "3"),
            "reason": "Search recency and browse depth",
        },
        {
            "user_id": "user_0004",
            "slot": "deals_strip",
            "item_id": "SKU-3044",
            "score": _stable_score(resolved_batch_date, model_version, "4"),
            "reason": "Seasonal promotion fit",
        },
    ]

    return {
        "batch_date": resolved_batch_date,
        "model_version": model_version,
        "users_covered": users_covered,
        "items_ranked": items_ranked,
        "preview": preview,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "message": "Recommendation batch generated and ready for preview.",
    }
