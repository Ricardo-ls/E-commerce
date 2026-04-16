from __future__ import annotations

import argparse
import json
import logging
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from tools_ecommerce_recommendation import generate_batch_snapshot

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "assistant.log"
STATE_FILE = DATA_DIR / "demo_state.json"

INITIAL_STATE: Dict[str, Any] = {
    "batch_snapshot": None,
    "publish_status": "draft",
    "audit_log": [],
}

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>E-commerce Batch Recommendation Demo</title>
  <style>
    :root {
      --bg: #f5f1e8;
      --panel: #fffaf2;
      --ink: #1f2430;
      --muted: #6e6a63;
      --accent: #b55233;
      --accent-soft: #efd7c4;
      --line: #decdbb;
      --ok: #2f7d4a;
      --warn: #a0621d;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(181,82,51,0.08), transparent 28%),
        linear-gradient(180deg, #f8f4ec 0%, #f0e7da 100%);
    }
    .wrap {
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px;
    }
    .hero {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: end;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 34px;
      line-height: 1.05;
    }
    .hero p {
      margin: 0;
      max-width: 720px;
      color: var(--muted);
    }
    .toolbar {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    button {
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--ink);
      padding: 10px 14px;
      border-radius: 999px;
      cursor: pointer;
      font: inherit;
    }
    button.primary {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }
    .status {
      margin-top: 12px;
      color: var(--muted);
      font-size: 14px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    .panel {
      background: rgba(255,250,242,0.92);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 18px;
      box-shadow: 0 12px 28px rgba(80, 49, 24, 0.08);
    }
    .panel h2 {
      margin: 0 0 12px;
      font-size: 20px;
    }
    .label {
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .metric {
      font-size: 30px;
      font-weight: 700;
      margin: 6px 0 14px;
    }
    .summary-grid, .control-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .tile, .item {
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 12px;
      background: rgba(255,255,255,0.52);
    }
    .item strong, .tile strong {
      display: block;
      margin-bottom: 4px;
    }
    .list {
      display: grid;
      gap: 10px;
    }
    .hint {
      color: var(--muted);
      font-size: 14px;
    }
    @media (max-width: 860px) {
      .grid, .summary-grid, .control-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div>
        <h1>E-commerce Batch Recommendation Demo</h1>
        <p>A minimal governed workflow for classroom or PPT demos: generate a nightly batch, preview the results, request publish, approve publish, and show the audit trail.</p>
        <div id="status" class="status">Ready.</div>
      </div>
      <div class="toolbar">
        <button class="primary" onclick="generateBatch()">Generate Batch</button>
        <button onclick="requestPublish()">Request Publish</button>
        <button onclick="approvePublish()">Approve Publish</button>
        <button onclick="refreshState()">Refresh</button>
      </div>
    </div>

    <div class="grid">
      <section class="panel">
        <h2>Batch Summary</h2>
        <div class="summary-grid">
          <div class="tile">
            <div class="label">Publish Status</div>
            <div id="publish-status" class="metric">draft</div>
          </div>
          <div class="tile">
            <div class="label">Batch Date</div>
            <div id="batch-date" class="metric">-</div>
          </div>
          <div class="tile">
            <strong>Model Version</strong>
            <div id="model-version">-</div>
          </div>
          <div class="tile">
            <strong>Users Covered</strong>
            <div id="users-covered">-</div>
          </div>
        </div>
      </section>

      <section class="panel">
        <h2>Publish Control</h2>
        <div class="control-grid">
          <div class="tile">
            <strong>Current Gate</strong>
            <div id="control-status">draft</div>
          </div>
          <div class="tile">
            <strong>Next Action</strong>
            <div id="next-action">Generate a batch first.</div>
          </div>
        </div>
        <div style="margin-top: 14px;" class="hint">
          This demo only keeps three states: <code>draft</code>, <code>pending_approval</code>, and <code>published</code>.
        </div>
      </section>

      <section class="panel">
        <h2>Recommendation Preview</h2>
        <div id="preview-list" class="list"></div>
      </section>

      <section class="panel">
        <h2>Audit Trail</h2>
        <div id="audit-list" class="list"></div>
      </section>
    </div>
  </div>

  <script>
    async function api(path, options = {}) {
      const res = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      return res.json();
    }

    function setStatus(text) {
      document.getElementById("status").textContent = text;
    }

    function formatRomeTime(timestampUtc) {
      const date = new Date(timestampUtc);
      const formatter = new Intl.DateTimeFormat("en-GB", {
        timeZone: "Europe/Rome",
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZoneName: "short",
      });
      return formatter.format(date).replace(",", "");
    }

    function renderPreview(rows) {
      const root = document.getElementById("preview-list");
      root.innerHTML = "";
      if (!rows.length) {
        root.innerHTML = '<div class="item"><strong>No recommendations yet</strong><div class="hint">Click Generate Batch to create a demo snapshot.</div></div>';
        return;
      }
      rows.forEach((row) => {
        const div = document.createElement("div");
        div.className = "item";
        div.innerHTML = `
          <strong>${row.user_id} → ${row.item_id}</strong>
          <div>${row.slot} · score ${row.score}</div>
          <div class="hint">${row.reason}</div>
        `;
        root.appendChild(div);
      });
    }

    function renderAudit(logs) {
      const root = document.getElementById("audit-list");
      root.innerHTML = "";
      if (!logs.length) {
        root.innerHTML = '<div class="item"><strong>No audit events yet</strong><div class="hint">Workflow actions will be listed here.</div></div>';
        return;
      }
      logs.slice().reverse().forEach((entry) => {
        const div = document.createElement("div");
        div.className = "item";
        div.innerHTML = `
          <strong>${entry.action}</strong>
          <div>${formatRomeTime(entry.timestamp_utc)}</div>
          <div class="hint">${entry.message}</div>
        `;
        root.appendChild(div);
      });
    }

    function renderState(state) {
      const snapshot = state.batch_snapshot || {};
      document.getElementById("publish-status").textContent = state.publish_status;
      document.getElementById("batch-date").textContent = snapshot.batch_date || "-";
      document.getElementById("model-version").textContent = snapshot.model_version || "-";
      document.getElementById("users-covered").textContent = snapshot.users_covered || "-";
      document.getElementById("control-status").textContent = state.publish_status;
      const nextAction = {
        draft: snapshot.batch_date ? "Request publish when preview looks correct." : "Generate a batch first.",
        pending_approval: "Approve publish to finish the governed release.",
        published: "Refresh or generate a new batch for the next cycle."
      };
      document.getElementById("next-action").textContent = nextAction[state.publish_status] || "-";
      renderPreview(snapshot.preview || []);
      renderAudit(state.audit_log || []);
    }

    async function refreshState() {
      const state = await api("/api/state");
      renderState(state);
      setStatus(`Loaded state: ${state.publish_status}`);
      return state;
    }

    async function generateBatch() {
      setStatus("Generating batch...");
      const state = await api("/api/generate", { method: "POST" });
      renderState(state);
      setStatus("Batch generated.");
    }

    async function requestPublish() {
      setStatus("Requesting publish...");
      const state = await api("/api/request_publish", { method: "POST" });
      renderState(state);
      setStatus("Publish request recorded.");
    }

    async function approvePublish() {
      setStatus("Approving publish...");
      const state = await api("/api/approve_publish", { method: "POST" });
      renderState(state);
      setStatus("Publish approved.");
    }

    refreshState().catch((err) => {
      setStatus(`Init failed: ${err.message}`);
    });
  </script>
</body>
</html>
"""


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("ecommerce_batch_demo")
    if logger.handlers:
        return
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def log_event(message: str) -> None:
    logging.getLogger("ecommerce_batch_demo").info(message)


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> Dict[str, Any]:
    ensure_data_dir()
    if not STATE_FILE.exists():
        save_state(INITIAL_STATE)
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: Dict[str, Any]) -> None:
    ensure_data_dir()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def reset_state() -> Dict[str, Any]:
    save_state(INITIAL_STATE)
    return load_state()


def append_audit_log(state: Dict[str, Any], action: str, message: str) -> Dict[str, Any]:
    updated = dict(state)
    audit_log = list(updated.get("audit_log", []))
    audit_log.append(
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "message": message,
        }
    )
    updated["audit_log"] = audit_log
    log_event(f"{action} | {message}")
    return updated


def generate_demo_batch() -> Dict[str, Any]:
    state = load_state()
    snapshot = generate_batch_snapshot()
    updated = {
        "batch_snapshot": snapshot,
        "publish_status": "draft",
        "audit_log": state.get("audit_log", []),
    }
    updated = append_audit_log(updated, "generate_batch", "Nightly batch snapshot generated for preview.")
    save_state(updated)
    return updated


def request_publish() -> Dict[str, Any]:
    state = load_state()
    if not state.get("batch_snapshot"):
        raise ValueError("Generate Batch first.")
    if state["publish_status"] == "pending_approval":
        raise ValueError("Publish request is already pending approval.")
    if state["publish_status"] == "published":
        raise ValueError("Batch is already published. Generate a new batch to restart the flow.")

    updated = dict(state)
    updated["publish_status"] = "pending_approval"
    updated = append_audit_log(updated, "request_publish", "Publish request submitted and waiting for approval.")
    save_state(updated)
    return updated


def approve_publish() -> Dict[str, Any]:
    state = load_state()
    if state["publish_status"] != "pending_approval":
        raise ValueError("Request Publish before approving.")

    updated = dict(state)
    updated["publish_status"] = "published"
    updated = append_audit_log(updated, "approve_publish", "Publish approved and snapshot marked as published.")
    save_state(updated)
    return updated


def get_demo_state() -> Dict[str, Any]:
    return load_state()


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "EcommerceBatchDemo/2.0"

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(INDEX_HTML)
            return
        if parsed.path == "/api/state":
            self._send_json(get_demo_state())
            return
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/generate":
                self._send_json(generate_demo_batch())
                return
            if parsed.path == "/api/request_publish":
                self._send_json(request_publish())
                return
            if parsed.path == "/api/approve_publish":
                self._send_json(approve_publish())
                return
            if parsed.path == "/api/reset":
                self._send_json(reset_state())
                return
            self._send_json({"error": "Not found"}, status=404)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=400)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def find_free_port(start: int = 8765, end: int = 8795) -> int:
    import socket

    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free port found in the configured range.")


def start_server(port: int | None = None, open_browser: bool = True) -> None:
    configure_logging()
    load_state()

    selected_port = port or find_free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", selected_port), RequestHandler)
    url = f"http://127.0.0.1:{selected_port}"
    print(f"Server running at {url}")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\nServer stopped.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minimal governed e-commerce batch recommendation demo.")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--generate", action="store_true", help="Generate a fresh demo batch.")
    parser.add_argument("--request-publish", action="store_true", help="Move the batch to pending approval.")
    parser.add_argument("--approve-publish", action="store_true", help="Approve the pending publish request.")
    parser.add_argument("--reset", action="store_true", help="Reset demo state.")
    args = parser.parse_args()

    configure_logging()

    if args.reset:
        print(json.dumps(reset_state(), indent=2, ensure_ascii=False))
    elif args.generate:
        print(json.dumps(generate_demo_batch(), indent=2, ensure_ascii=False))
    elif args.request_publish:
        print(json.dumps(request_publish(), indent=2, ensure_ascii=False))
    elif args.approve_publish:
        print(json.dumps(approve_publish(), indent=2, ensure_ascii=False))
    else:
        start_server(args.port, open_browser=not args.no_browser)
