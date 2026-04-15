from __future__ import annotations

import json
from app_ecommerce_recommendation_ui import demo_flow, get_dashboard_state, configure_logging


if __name__ == "__main__":
    configure_logging()
    outputs = demo_flow("test")
    state = get_dashboard_state("test")
    print("=== FULL DEMO OUTPUT ===")
    print(json.dumps(outputs, indent=2, ensure_ascii=False))
    print("\n=== DASHBOARD STATE ===")
    print(json.dumps(state, indent=2, ensure_ascii=False))
