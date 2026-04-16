from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app_ecommerce_recommendation_ui as app


class MinimalGovernedDemoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.data_dir = self.base / "data"
        self.log_dir = self.base / "logs"

        self.patcher = patch.multiple(
            app,
            BASE_DIR=self.base,
            DATA_DIR=self.data_dir,
            LOG_DIR=self.log_dir,
            LOG_FILE=self.log_dir / "assistant.log",
            STATE_FILE=self.data_dir / "demo_state.json",
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        logger = logging.getLogger("ecommerce_batch_demo")
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()

        app.configure_logging()

    def test_generate_batch_creates_snapshot_and_audit_event(self) -> None:
        state = app.generate_demo_batch()

        self.assertEqual(state["publish_status"], "draft")
        self.assertIsNotNone(state["batch_snapshot"])
        self.assertEqual(len(state["batch_snapshot"]["preview"]), 4)
        self.assertEqual(state["audit_log"][-1]["action"], "generate_batch")

    def test_request_publish_moves_state_to_pending_approval(self) -> None:
        app.generate_demo_batch()
        state = app.request_publish()

        self.assertEqual(state["publish_status"], "pending_approval")
        self.assertEqual(state["audit_log"][-1]["action"], "request_publish")

    def test_approve_publish_finishes_closed_loop(self) -> None:
        app.generate_demo_batch()
        app.request_publish()
        state = app.approve_publish()

        self.assertEqual(state["publish_status"], "published")
        self.assertEqual(state["audit_log"][-1]["action"], "approve_publish")

    def test_publish_actions_require_expected_order(self) -> None:
        with self.assertRaisesRegex(ValueError, "Generate Batch first"):
            app.request_publish()

        app.generate_demo_batch()
        with self.assertRaisesRegex(ValueError, "Request Publish before approving"):
            app.approve_publish()

    def test_state_round_trip_persists_to_json_file(self) -> None:
        app.generate_demo_batch()
        app.request_publish()

        state = app.get_demo_state()
        self.assertEqual(state["publish_status"], "pending_approval")
        self.assertTrue(app.STATE_FILE.exists())


if __name__ == "__main__":
    unittest.main()
