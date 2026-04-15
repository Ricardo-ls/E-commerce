from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass(frozen=True)
class ToolSpec:
    name: str
    stage: str
    description: str
    requires_human_review: bool
    function: Callable[..., Dict[str, Any]]


def _stable_ratio(*parts: str) -> float:
    payload = "|".join(parts).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:8]
    return int(digest, 16) / 0xFFFFFFFF


def _stable_int(low: int, high: int, *parts: str) -> int:
    ratio = _stable_ratio(*parts)
    return low + int((high - low) * ratio)


def _stable_float(low: float, high: float, *parts: str) -> float:
    ratio = _stable_ratio(*parts)
    return round(low + (high - low) * ratio, 4)


def collect_behavior_batch(batch_date: str, user_segment: str = "all_users") -> Dict[str, Any]:
    records_collected = _stable_int(1180000, 1360000, batch_date, user_segment, "collect")
    return {
        "batch_date": batch_date,
        "user_segment": user_segment,
        "records_collected": records_collected,
        "signals": [
            "click_history",
            "browse_history",
            "watch_time",
            "search_terms",
            "interaction_logs",
            "cart_events",
            "purchase_feedback",
        ],
        "message": "Nightly e-commerce behavior batch collected and staged.",
    }


def validate_and_prepare_batch(batch_date: str) -> Dict[str, Any]:
    filtered_records = _stable_int(15000, 28000, batch_date, "validate")
    anonymized_records = _stable_int(1180000, 1360000, batch_date, "anonymize") - filtered_records
    return {
        "batch_date": batch_date,
        "status": "validated",
        "checks": {
            "schema_validation": True,
            "missing_value_filter": True,
            "outlier_skip": True,
            "identifier_removed": True,
            "feature_minimization": True,
            "sensitive_brand_flagging": True,
        },
        "filtered_records": filtered_records,
        "records_ready_for_inference": anonymized_records,
        "message": "Batch data validated, anonymized, minimized, and prepared for recommendation inference.",
    }


def run_batch_inference(batch_date: str, model_version: str, top_k: int = 20) -> Dict[str, Any]:
    users_scored = _stable_int(1160000, 1330000, batch_date, model_version, "score")
    candidate_items = _stable_int(22000000, 31000000, batch_date, model_version, "candidates")
    manual_review_queue = _stable_int(800, 2200, batch_date, model_version, "review")
    return {
        "batch_date": batch_date,
        "model_version": model_version,
        "top_k": top_k,
        "estimated_users_scored": users_scored,
        "candidate_items_generated": candidate_items,
        "manual_review_queue": manual_review_queue,
        "runtime_optimization": {
            "dynamic_batching": True,
            "kv_cache": True,
            "precompute_to_database": True,
        },
        "transparency_summary": {
            "primary_drivers": [
                "recent clicks",
                "watch time",
                "search recency",
                "cart interactions",
            ],
            "user_explanation_available": True,
        },
        "fairness_monitor": {
            "age_group_exposure_gap": _stable_float(0.01, 0.07, batch_date, model_version, "age_gap"),
            "region_exposure_gap": _stable_float(0.01, 0.06, batch_date, model_version, "region_gap"),
            "diversity_index": _stable_float(0.72, 0.91, batch_date, model_version, "diversity"),
        },
        "message": "Nightly batch inference finished and governed recommendation candidates were generated.",
    }


def store_recommendation_snapshot(
    batch_date: str,
    model_version: str,
    storage_target: str = "recommendation_snapshot_db",
) -> Dict[str, Any]:
    stored_rows = _stable_int(1150000, 1320000, batch_date, model_version, "store")
    return {
        "batch_date": batch_date,
        "model_version": model_version,
        "storage_target": storage_target,
        "stored_rows": stored_rows,
        "status": "stored",
        "message": "Recommendation snapshot stored for next-day homepage and video serving.",
    }


def publish_recommendation_snapshot(batch_date: str, surface: str, model_version: str) -> Dict[str, Any]:
    published_impressions = _stable_int(3000000, 5800000, batch_date, model_version, surface, "publish")
    return {
        "batch_date": batch_date,
        "surface": surface,
        "model_version": model_version,
        "published_impression_budget": published_impressions,
        "status": "published_in_simulation",
        "message": "Recommendation snapshot published to the user-facing surface after operator approval.",
    }


def inspect_audit_summary(batch_date: str) -> Dict[str, Any]:
    return {
        "batch_date": batch_date,
        "summary_fields": [
            "records_collected",
            "records_ready_for_inference",
            "model_version",
            "manual_review_queue",
            "fairness_monitor",
            "transparency_summary",
            "storage_target",
            "publication_status",
            "environment",
            "operator_approval",
        ],
        "message": "Audit summary generated for monitoring, review, and traceability.",
    }


TOOL_REGISTRY: Dict[str, ToolSpec] = {
    "collect_behavior_batch": ToolSpec(
        name="collect_behavior_batch",
        stage="data_collection",
        description="Collect nightly e-commerce user-behavior data for batch recommendation.",
        requires_human_review=False,
        function=collect_behavior_batch,
    ),
    "validate_and_prepare_batch": ToolSpec(
        name="validate_and_prepare_batch",
        stage="data_governance",
        description="Validate, anonymize, and minimize recommendation input data.",
        requires_human_review=False,
        function=validate_and_prepare_batch,
    ),
    "run_batch_inference": ToolSpec(
        name="run_batch_inference",
        stage="model_inference",
        description="Run nightly batch inference for recommendation candidate generation.",
        requires_human_review=False,
        function=run_batch_inference,
    ),
    "store_recommendation_snapshot": ToolSpec(
        name="store_recommendation_snapshot",
        stage="snapshot_storage",
        description="Store the recommendation snapshot for next-day serving.",
        requires_human_review=False,
        function=store_recommendation_snapshot,
    ),
    "publish_recommendation_snapshot": ToolSpec(
        name="publish_recommendation_snapshot",
        stage="user_facing_rollout",
        description="Publish the prepared recommendation snapshot to homepage or video surfaces.",
        requires_human_review=True,
        function=publish_recommendation_snapshot,
    ),
    "inspect_audit_summary": ToolSpec(
        name="inspect_audit_summary",
        stage="audit_review",
        description="Inspect audit fields for governance, monitoring, and traceability.",
        requires_human_review=False,
        function=inspect_audit_summary,
    ),
}
