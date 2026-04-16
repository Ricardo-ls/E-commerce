#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 app_ecommerce_recommendation_ui.py --reset >/dev/null
python3 app_ecommerce_recommendation_ui.py
