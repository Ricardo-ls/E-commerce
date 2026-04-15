#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 app_ecommerce_recommendation_ui.py --seed --environment test >/dev/null
python3 app_ecommerce_recommendation_ui.py
