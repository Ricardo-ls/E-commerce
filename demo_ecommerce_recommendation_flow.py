from __future__ import annotations

import json

from app_ecommerce_recommendation_ui import (
    approve_publish,
    configure_logging,
    generate_demo_batch,
    get_demo_state,
    request_publish,
    reset_state,
)


if __name__ == "__main__":
    configure_logging()
    reset_state()
    generate_demo_batch()
    request_publish()
    approve_publish()
    print(json.dumps(get_demo_state(), indent=2, ensure_ascii=False))
