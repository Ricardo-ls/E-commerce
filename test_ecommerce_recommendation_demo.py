from __future__ import annotations

import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app_ecommerce_recommendation_ui as app


class GovernedDemoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.data_dir = self.base / "data"
        self.log_dir = self.base / "logs"
        self.test_dir = self.data_dir / "test"
        self.prod_dir = self.data_dir / "production"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.prod_dir.mkdir(parents=True, exist_ok=True)

        self.patcher = patch.multiple(
            app,
            BASE_DIR=self.base,
            DATA_DIR=self.data_dir,
            LOG_DIR=self.log_dir,
            LOG_FILE=self.log_dir / "assistant.log",
            ENVIRONMENTS={"test": self.test_dir, "production": self.prod_dir},
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        logger = logging.getLogger("ecommerce_batch_demo")
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()

    def test_force_seed_populates_dashboard(self) -> None:
        result = app.force_seed_demo_content("test")
        state = result["dashboard_state"]

        self.assertEqual(result["status"], "force_seeded")
        self.assertGreaterEqual(len(state["recent_records"]), 6)
        self.assertGreaterEqual(len(state["pending_releases"]), 1)
        self.assertIsNotNone(state["monitor_summary"]["latest_users_scored"])
        self.assertTrue(state["latest_snapshot_preview"])

    def test_state_is_empty_before_seeding(self) -> None:
        initial = app.get_dashboard_state("test")
        self.assertEqual(initial["recent_records"], [])
        self.assertEqual(initial["pending_releases"], [])

        seeded = app.force_seed_demo_content("test")
        self.assertGreater(len(seeded["dashboard_state"]["recent_records"]), 0)

    def test_preview_contains_rows_from_latest_inference(self) -> None:
        app.force_seed_demo_content("test")
        preview = app.get_dashboard_state("test")["latest_snapshot_preview"]

        self.assertEqual(len(preview), 5)
        self.assertTrue(all("user_id" in row for row in preview))
        self.assertTrue(all("surface" in row for row in preview))

    def test_tool_result_has_dashboard_fields(self) -> None:
        output = app.run_assistant("Run recommendation inference for 2026-04-15 with model v2.3", "test")
        record_path = Path(output["result"]["record_path"])
        payload = json.loads(record_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["tool_name"], "run_batch_inference")
        self.assertIn("estimated_users_scored", payload["result"])
        self.assertIn("manual_review_queue", payload["result"])
        self.assertIn("fairness_monitor", payload["result"])


if __name__ == "__main__":
    unittest.main()
