from __future__ import annotations

import argparse
import json
import logging
import re
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse

from tools_ecommerce_recommendation import TOOL_REGISTRY

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "assistant.log"
ENVIRONMENTS = {
    "test": DATA_DIR / "test",
    "production": DATA_DIR / "production",
}
PENDING_DIRNAME = "pending_releases"

_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
_MODEL_RE = re.compile(r"\b(v\d+(?:\.\d+)?)\b", re.IGNORECASE)


@dataclass
class AssistantDecision:
    tool_name: str
    intent: str
    stage: str
    params: Dict[str, Any]


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Governed E-commerce Batch Recommendation Demo</title>
  <style>
    :root {
      --bg: #0b1020;
      --panel: #131a2e;
      --panel-2: #18213a;
      --text: #edf2ff;
      --muted: #a4afcf;
      --accent: #6ea8fe;
      --accent-2: #70e1b5;
      --warn: #ffcf66;
      --danger: #ff8787;
      --border: rgba(255,255,255,0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #0b1020 0%, #0d1326 100%);
      color: var(--text);
    }
    .wrap {
      max-width: 1450px;
      margin: 0 auto;
      padding: 24px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }
    .title h1 {
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.1;
    }
    .title p {
      margin: 0;
      color: var(--muted);
      max-width: 900px;
    }
    .toolbar {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }
    select, textarea, button, input {
      border-radius: 14px;
      border: 1px solid var(--border);
      background: var(--panel);
      color: var(--text);
      font: inherit;
    }
    select, input {
      padding: 10px 12px;
    }
    textarea {
      width: 100%;
      min-height: 140px;
      padding: 14px;
      resize: vertical;
    }
    button {
      padding: 10px 14px;
      cursor: pointer;
      background: var(--panel-2);
      transition: transform .12s ease, border-color .12s ease;
    }
    button.primary {
      background: linear-gradient(135deg, rgba(110,168,254,0.24), rgba(112,225,181,0.18));
      border-color: rgba(110,168,254,0.35);
    }
    button:hover { transform: translateY(-1px); }
    .grid {
      display: grid;
      grid-template-columns: 1.25fr 1fr;
      gap: 16px;
    }
    .cards {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      margin-bottom: 16px;
    }
    .card, .panel {
      background: rgba(19,26,46,0.96);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.18);
    }
    .metric {
      font-size: 28px;
      font-weight: 700;
      margin: 8px 0 2px;
    }
    .label, .subtle {
      color: var(--muted);
      font-size: 13px;
    }
    .panel h2 {
      margin: 0 0 12px;
      font-size: 18px;
    }
    .panel h3 {
      margin: 18px 0 10px;
      font-size: 15px;
    }
    .chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }
    .chip {
      padding: 8px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--border);
      color: var(--muted);
      cursor: pointer;
      font-size: 13px;
    }
    .list {
      display: grid;
      gap: 10px;
    }
    .item {
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 12px;
      background: rgba(255,255,255,0.03);
    }
    .item strong { display: block; margin-bottom: 4px; }
    .row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 12px;
      color: #d9e2ff;
    }
    .small-btn {
      padding: 8px 10px;
      border-radius: 12px;
      font-size: 13px;
    }
    .log-box, .json-box {
      max-height: 280px;
      overflow: auto;
      padding: 12px;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: #0b1120;
    }
    .split {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }
    .full-width {
      grid-column: 1 / -1;
    }
    .status {
      font-size: 12px;
      color: var(--accent-2);
    }
    .warn { color: var(--warn); }
    .danger { color: var(--danger); }
    @media (max-width: 1120px) {
      .cards { grid-template-columns: repeat(2, 1fr); }
      .grid, .split { grid-template-columns: 1fr; }
    }
    @media (max-width: 680px) {
      .cards { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div class="title">
        <h1>Governed E-commerce Batch Recommendation Demo</h1>
        <p>Natural-language control for a nightly batch recommendation workflow with environment isolation, approval gating, monitoring, audit records, and log traceability.</p>
      </div>
      <div class="toolbar">
        <select id="environment">
          <option value="test">test</option>
          <option value="production">production</option>
        </select>
        <button onclick="seedDemo()">Generate Test Data</button>
        <button class="primary" onclick="runFullDemo()">Run Full Nightly Job</button>
        <button onclick="refreshState()">Refresh State</button>
      </div>
    </div>

    <div class="cards">
      <div class="card"><div class="label">Recent records</div><div id="metric-records" class="metric">0</div><div class="subtle">Saved JSON artifacts</div></div>
      <div class="card"><div class="label">Pending approvals</div><div id="metric-pending" class="metric">0</div><div class="subtle">Release gates waiting for operator action</div></div>
      <div class="card"><div class="label">Latest users scored</div><div id="metric-users" class="metric">-</div><div class="subtle">From most recent inference run</div></div>
      <div class="card"><div class="label">Manual review queue</div><div id="metric-review" class="metric">-</div><div class="subtle">Sensitive recommendations awaiting review</div></div>
    </div>

    <div class="grid">
      <div class="panel">
        <h2>Natural-language command center</h2>
        <textarea id="instruction">Collect nightly behavior batch for 2026-04-15</textarea>
        <div class="chip-row">
          <div class="chip" onclick="setInstruction('Collect nightly behavior batch for 2026-04-15')">Collect batch</div>
          <div class="chip" onclick="setInstruction('Validate and prepare batch for 2026-04-15')">Validate batch</div>
          <div class="chip" onclick="setInstruction('Run recommendation inference for 2026-04-15 with model v2.3')">Run inference</div>
          <div class="chip" onclick="setInstruction('Store recommendation snapshot for 2026-04-15 with model v2.3')">Store snapshot</div>
          <div class="chip" onclick="setInstruction('Publish recommendation snapshot for 2026-04-15 to homepage with model v2.3')">Request publish</div>
          <div class="chip" onclick="setInstruction('Inspect audit summary for 2026-04-15')">Inspect audit</div>
        </div>
        <div class="toolbar" style="margin-top: 14px;">
          <button class="primary" onclick="runInstruction()">Run Instruction</button>
          <span id="last-status" class="status">Ready.</span>
        </div>

        <h3>Latest API response</h3>
        <div class="json-box"><pre id="latest-response">{}</pre></div>
      </div>

      <div class="panel">
        <h2>Pending release approvals</h2>
        <div id="pending-list" class="list"></div>

        <h3>Monitoring summary</h3>
        <div id="monitor-summary" class="list"></div>
      </div>
    </div>

    <div class="split" style="margin-top: 16px;">
      <div class="panel">
        <h2>Recent audit artifacts</h2>
        <div id="records-list" class="list"></div>
      </div>
      <div class="panel">
        <h2>Recent log tail</h2>
        <div class="log-box"><pre id="log-tail"></pre></div>
      </div>
    </div>

    <div class="panel full-width" style="margin-top: 16px;">
      <h2>Latest recommendation preview</h2>
      <div class="subtle">A concrete sample of scored recommendation rows from the latest batch inference run.</div>
      <div id="preview-list" class="list" style="margin-top: 12px;"></div>
    </div>
  </div>

  <script>
    async function api(path, options = {}) {
      const res = await fetch(path, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      return res.json();
    }

    function env() {
      return document.getElementById('environment').value;
    }

    function setInstruction(value) {
      document.getElementById('instruction').value = value;
    }

    function showResponse(obj) {
      document.getElementById('latest-response').textContent = JSON.stringify(obj, null, 2);
    }

    function setStatus(text, cls = 'status') {
      const el = document.getElementById('last-status');
      el.className = cls;
      el.textContent = text;
    }

    function renderPending(items) {
      const root = document.getElementById('pending-list');
      root.innerHTML = '';
      if (!items.length) {
        root.innerHTML = '<div class="item"><strong>No pending approvals</strong><div class="subtle">User-facing publication gates will appear here.</div></div>';
        return;
      }
      items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'item';
        div.innerHTML = `
          <div class="row">
            <div>
              <strong>${item.release_id}</strong>
              <div class="subtle">${item.tool_name} · ${item.environment}</div>
              <div class="subtle">${item.params.batch_date} · ${item.params.surface || 'homepage_feed'} · ${item.params.model_version || '-'}</div>
            </div>
            <div>
              <button class="small-btn primary" onclick="approveRelease('${item.release_id}')">Approve publish</button>
            </div>
          </div>
        `;
        root.appendChild(div);
      });
    }

    function renderMonitor(summary) {
      const root = document.getElementById('monitor-summary');
      root.innerHTML = '';
      const cards = [
        ['Users scored', summary.latest_users_scored ?? '-'],
        ['Manual review queue', summary.latest_manual_review_queue ?? '-'],
        ['Age-group exposure gap', summary.age_group_exposure_gap ?? '-'],
        ['Region exposure gap', summary.region_exposure_gap ?? '-'],
        ['Diversity index', summary.diversity_index ?? '-'],
        ['Latest model', summary.latest_model_version ?? '-'],
        ['Latest publication status', summary.latest_publication_status ?? '-'],
      ];
      cards.forEach(([label, value]) => {
        const div = document.createElement('div');
        div.className = 'item';
        div.innerHTML = `<strong>${label}</strong><div>${value}</div>`;
        root.appendChild(div);
      });
    }

    function renderRecords(items) {
      const root = document.getElementById('records-list');
      root.innerHTML = '';
      if (!items.length) {
        root.innerHTML = '<div class="item"><strong>No records yet</strong><div class="subtle">Run a stage to generate environment-isolated JSON artifacts.</div></div>';
        return;
      }
      items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'item';
        div.innerHTML = `
          <strong>${item.filename}</strong>
          <div class="subtle">tool: ${item.tool_name} · stage: ${item.stage} · approved: ${item.user_approved}</div>
          <div class="subtle">${item.timestamp_utc || '-'}</div>
        `;
        root.appendChild(div);
      });
    }

    function renderPreview(rows) {
      const root = document.getElementById('preview-list');
      root.innerHTML = '';
      if (!rows.length) {
        root.innerHTML = '<div class="item"><strong>No preview rows yet</strong><div class="subtle">Run test data generation or batch inference to populate sample recommendations.</div></div>';
        return;
      }
      rows.forEach(row => {
        const div = document.createElement('div');
        div.className = 'item';
        div.innerHTML = `
          <div class="row">
            <div>
              <strong>${row.user_id}</strong>
              <div class="subtle">surface: ${row.surface} · segment: ${row.segment} · score: ${row.score}</div>
            </div>
            <div class="subtle">${row.reason}</div>
          </div>
        `;
        root.appendChild(div);
      });
    }

    function renderState(state) {
      document.getElementById('metric-records').textContent = state.recent_records.length;
      document.getElementById('metric-pending').textContent = state.pending_releases.length;
      document.getElementById('metric-users').textContent = state.monitor_summary.latest_users_scored ?? '-';
      document.getElementById('metric-review').textContent = state.monitor_summary.latest_manual_review_queue ?? '-';
      renderPending(state.pending_releases);
      renderMonitor(state.monitor_summary);
      renderRecords(state.recent_records);
      renderPreview(state.latest_snapshot_preview || []);
      document.getElementById('log-tail').textContent = state.log_tail.join('\\n');
    }

    async function refreshState() {
      try {
        const state = await api(`/api/state?environment=${encodeURIComponent(env())}`);
        renderState(state);
        return state;
      } catch (err) {
        setStatus(`Refresh failed: ${err.message}`, 'warn');
        throw err;
      }
    }

    async function runInstruction() {
      try {
        setStatus('Running instruction...');
        const payload = { environment: env(), instruction: document.getElementById('instruction').value };
        const result = await api('/api/run', { method: 'POST', body: JSON.stringify(payload) });
        showResponse(result);
        setStatus(`Instruction completed: ${result.status}`);
        await refreshState();
      } catch (err) {
        setStatus(`Run failed: ${err.message}`, 'danger');
      }
    }

    async function runFullDemo() {
      try {
        setStatus('Running full nightly job...');
        const result = await api('/api/full_demo', {
          method: 'POST',
          body: JSON.stringify({ environment: env() })
        });
        showResponse(result);
        if (result.dashboard_state) {
          renderState(result.dashboard_state);
        } else {
          await refreshState();
        }
        setStatus('Full nightly job completed.');
      } catch (err) {
        setStatus(`Full demo failed: ${err.message}`, 'danger');
      }
    }

    async function seedDemo() {
      try {
        setStatus('Generating test data...');
        const result = await api('/api/seed', {
          method: 'POST',
          body: JSON.stringify({ environment: env() })
        });
        showResponse(result);
        if (result.dashboard_state) {
          renderState(result.dashboard_state);
        } else {
          await refreshState();
        }
        setStatus('Test data generated.');
      } catch (err) {
        setStatus(`Seed failed: ${err.message}`, 'danger');
      }
    }

    async function approveRelease(releaseId) {
      try {
        setStatus(`Approving ${releaseId}...`);
        const result = await api('/api/approve', {
          method: 'POST',
          body: JSON.stringify({ release_id: releaseId })
        });
        showResponse(result);
        setStatus(`Approved: ${releaseId}`);
        await refreshState();
      } catch (err) {
        setStatus(`Approval failed: ${err.message}`, 'danger');
      }
    }

    document.getElementById('environment').addEventListener('change', async () => {
      try {
        const state = await refreshState();
        if (!state.recent_records.length && !state.pending_releases.length) {
          await seedDemo();
        }
      } catch (err) {
        setStatus(`Environment switch failed: ${err.message}`, 'danger');
      }
    });

    (async function initPage() {
      try {
        const state = await refreshState();
        if (!state.recent_records.length && !state.pending_releases.length) {
          await seedDemo();
        }
      } catch (err) {
        setStatus(`Init failed: ${err.message}`, 'danger');
      }
    })();
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
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(tool_name)s | %(stage)s | %(action)s | %(message)s"
        )
    )
    logger.addHandler(handler)
    logger.propagate = False


def log_event(tool_name: str, stage: str, action: str, message: str) -> None:
    logging.getLogger("ecommerce_batch_demo").info(
        message,
        extra={"tool_name": tool_name, "stage": stage, "action": action},
    )


def resolve_environment(environment: str) -> Path:
    if environment not in ENVIRONMENTS:
        raise ValueError("environment must be 'test' or 'production'.")
    out_dir = ENVIRONMENTS[environment]
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def pending_dir(environment: str) -> Path:
    directory = resolve_environment(environment) / PENDING_DIRNAME
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def clear_environment_data(environment: str) -> None:
    env_dir = resolve_environment(environment)
    for file_path in env_dir.glob("*.json"):
        if file_path.is_file():
            file_path.unlink()

    pdir = pending_dir(environment)
    for file_path in pdir.glob("*.json"):
        if file_path.is_file():
            file_path.unlink()


def save_record(record_type: str, environment: str, payload: Dict[str, Any]) -> str:
    out_dir = resolve_environment(environment)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    file_path = out_dir / f"{record_type}_{timestamp}.json"
    file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(file_path)


def save_pending_release(release_id: str, environment: str, payload: Dict[str, Any]) -> str:
    file_path = pending_dir(environment) / f"{release_id}.json"
    file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(file_path)


def load_pending_release(release_id: str) -> Dict[str, Any] | None:
    for env_name in ENVIRONMENTS:
        file_path = pending_dir(env_name) / f"{release_id}.json"
        if file_path.exists():
            return json.loads(file_path.read_text(encoding="utf-8"))
    return None


def delete_pending_release(release_id: str, environment: str) -> None:
    file_path = pending_dir(environment) / f"{release_id}.json"
    if file_path.exists():
        file_path.unlink()


def extract_batch_date(text: str) -> str:
    match = _DATE_RE.search(text)
    if match:
        return match.group(1)
    return datetime.now().strftime("%Y-%m-%d")


def extract_model_version(text: str) -> str:
    match = _MODEL_RE.search(text)
    if match:
        return match.group(1)
    return "v2.3"


def classify_instruction(instruction: str) -> AssistantDecision:
    text = instruction.strip()
    lowered = text.lower()
    batch_date = extract_batch_date(text)
    model_version = extract_model_version(text)

    if any(k in lowered for k in ["collect", "收集", "采集"]):
        return AssistantDecision(
            tool_name="collect_behavior_batch",
            intent="collect_nightly_behavior_batch",
            stage=TOOL_REGISTRY["collect_behavior_batch"].stage,
            params={"batch_date": batch_date, "user_segment": "all_users"},
        )

    if any(k in lowered for k in ["validate", "校验", "prepare", "匿名", "治理"]):
        return AssistantDecision(
            tool_name="validate_and_prepare_batch",
            intent="validate_and_prepare_batch",
            stage=TOOL_REGISTRY["validate_and_prepare_batch"].stage,
            params={"batch_date": batch_date},
        )

    if any(k in lowered for k in ["publish", "发布", "上线", "rollout"]):
        surface = "homepage_feed"
        if "video" in lowered or "视频" in lowered:
            surface = "video_recommendation"
        return AssistantDecision(
            tool_name="publish_recommendation_snapshot",
            intent="publish_recommendation_snapshot",
            stage=TOOL_REGISTRY["publish_recommendation_snapshot"].stage,
            params={"batch_date": batch_date, "surface": surface, "model_version": model_version},
        )

    if any(k in lowered for k in ["store", "snapshot", "存储", "入库"]):
        return AssistantDecision(
            tool_name="store_recommendation_snapshot",
            intent="store_recommendation_snapshot",
            stage=TOOL_REGISTRY["store_recommendation_snapshot"].stage,
            params={
                "batch_date": batch_date,
                "model_version": model_version,
                "storage_target": "recommendation_snapshot_db",
            },
        )

    if any(k in lowered for k in ["inference", "推理", "recommend", "推荐", "score", "打分"]):
        return AssistantDecision(
            tool_name="run_batch_inference",
            intent="run_nightly_batch_inference",
            stage=TOOL_REGISTRY["run_batch_inference"].stage,
            params={"batch_date": batch_date, "model_version": model_version, "top_k": 20},
        )

    return AssistantDecision(
        tool_name="inspect_audit_summary",
        intent="inspect_audit_summary",
        stage=TOOL_REGISTRY["inspect_audit_summary"].stage,
        params={"batch_date": batch_date},
    )


def build_record(
    tool_name: str,
    environment: str,
    action: str,
    params: Dict[str, Any],
    result: Dict[str, Any],
    user_approved: bool,
) -> Dict[str, Any]:
    spec = TOOL_REGISTRY[tool_name]
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "stage": spec.stage,
        "environment": environment,
        "action": action,
        "requires_human_review": spec.requires_human_review,
        "user_approved": user_approved,
        "params": params,
        "result": result,
        "governance_controls": {
            "human_agency_and_oversight": "User-facing publication is approval-gated before rollout.",
            "technical_robustness_and_safety": "Validation, storage, and publication stages are independently recorded.",
            "privacy_and_data_governance": "The staged pipeline uses anonymization and data minimization before inference.",
            "transparency": "Model version, batch date, target surface, and explanation summary are stored.",
            "diversity_non_discrimination_and_fairness": "Fairness slice metrics are attached to inference records for review.",
            "societal_and_environmental_well_being": "Recommendation rollout is controlled rather than blindly auto-published.",
            "accountability": "Every stage leaves environment-specific JSON records and log traces.",
        },
    }


def execute_tool(
    tool_name: str,
    *,
    environment: str,
    action: str,
    user_approved: bool = False,
    **params: Any,
) -> Dict[str, Any]:
    spec = TOOL_REGISTRY[tool_name]

    if spec.requires_human_review and not user_approved:
        result = {
            "status": "blocked_pending_approval",
            "message": "User-facing recommendation publication requires explicit operator approval.",
        }
        record = build_record(tool_name, environment, action, params, result, user_approved)
        record_path = save_record(tool_name, environment, record)
        log_event(tool_name, spec.stage, action, result["message"])
        result["record_path"] = record_path
        return result

    result = spec.function(**params)
    record = build_record(tool_name, environment, action, params, result, user_approved)
    record_path = save_record(tool_name, environment, record)
    log_event(tool_name, spec.stage, action, result.get("message", "Tool executed."))
    result["record_path"] = record_path
    return result


def run_assistant(instruction: str, environment: str = "test") -> Dict[str, Any]:
    decision = classify_instruction(instruction)
    spec = TOOL_REGISTRY[decision.tool_name]
    log_event(decision.tool_name, spec.stage, "classified", f"Instruction classified as {decision.intent}.")

    if spec.requires_human_review:
        preview = execute_tool(
            decision.tool_name,
            environment=environment,
            action="approval_requested",
            user_approved=False,
            **decision.params,
        )
        release_id = f"release-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        pending_payload = {
            "environment": environment,
            "params": decision.params,
            "tool_name": decision.tool_name,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        pending_file = save_pending_release(release_id, environment, pending_payload)
        return {
            "status": "awaiting_approval",
            "decision": asdict(decision),
            "preview": preview,
            "release_id": release_id,
            "pending_file": pending_file,
        }

    result = execute_tool(
        decision.tool_name,
        environment=environment,
        action="executed",
        user_approved=False,
        **decision.params,
    )
    return {"status": "completed", "decision": asdict(decision), "result": result}


def approve_release(release_id: str) -> Dict[str, Any]:
    pending = load_pending_release(release_id)
    if not pending:
        raise KeyError(f"Unknown release_id: {release_id}")

    tool_name = pending["tool_name"]
    params = pending["params"]
    environment = pending["environment"]
    result = execute_tool(
        tool_name,
        environment=environment,
        action="approved_and_executed",
        user_approved=True,
        **params,
    )
    delete_pending_release(release_id, environment)
    return {"status": "completed_after_approval", "release_id": release_id, "result": result}


def demo_flow(environment: str = "test") -> Dict[str, Any]:
    configure_logging()
    outputs: Dict[str, Any] = {}
    batch_date = datetime.now().strftime("%Y-%m-%d")
    outputs["collect"] = run_assistant(f"Collect nightly behavior batch for {batch_date}", environment)
    outputs["validate"] = run_assistant(f"Validate and prepare batch for {batch_date}", environment)
    outputs["inference"] = run_assistant(
        f"Run recommendation inference for {batch_date} with model v2.3", environment
    )
    outputs["store"] = run_assistant(
        f"Store recommendation snapshot for {batch_date} with model v2.3", environment
    )
    publish_request = run_assistant(
        f"Publish recommendation snapshot for {batch_date} to homepage with model v2.3", environment
    )
    outputs["publish_request"] = publish_request
    outputs["publish_approved"] = approve_release(publish_request["release_id"])
    outputs["audit"] = run_assistant(f"Inspect audit summary for {batch_date}", environment)
    return outputs


def _build_recommendation_preview(environment: str) -> List[Dict[str, Any]]:
    inference_record = _latest_record_by_tool(environment, "run_batch_inference")
    publish_record = _latest_record_by_tool(environment, "publish_recommendation_snapshot")
    if not inference_record:
        return []

    result = inference_record.get("result", {})
    batch_date = result.get("batch_date") or inference_record.get("params", {}).get("batch_date")
    model_version = result.get("model_version") or inference_record.get("params", {}).get("model_version")
    surface = None
    if publish_record:
        surface = publish_record.get("params", {}).get("surface")
    if not surface:
        surface = "homepage_feed"

    manual_queue = result.get("manual_review_queue", 0)
    diversity = result.get("fairness_monitor", {}).get("diversity_index")

    return [
        {
            "user_id": f"user_{idx + 1:04d}",
            "surface": surface,
            "segment": segment,
            "score": score,
            "reason": reason,
            "batch_date": batch_date,
            "model_version": model_version,
        }
        for idx, (segment, score, reason) in enumerate([
            ("high_affinity", "0.982", "recent clicks + watch-time lift"),
            ("returning_buyer", "0.951", "cart and purchase feedback"),
            ("video_first", "0.944", "video engagement and search recency"),
            ("discovery", "0.917", f"diversity index {diversity}"),
            ("long_tail", "0.903", f"manual review queue {manual_queue}"),
        ])
    ]


def seed_demo_content(environment: str = "test") -> Dict[str, Any]:
    configure_logging()
    env_dir = resolve_environment(environment)
    existing = list(env_dir.glob("*.json"))
    existing_pending = list(pending_dir(environment).glob("*.json"))
    if existing and existing_pending:
        return {
            "status": "already_seeded",
            "environment": environment,
            "records": len(existing),
            "pending_releases": len(existing_pending),
            "dashboard_state": get_dashboard_state(environment),
        }

    outputs = demo_flow(environment)
    batch_date = datetime.now().strftime("%Y-%m-%d")
    pending_publish = run_assistant(
        f"Publish recommendation snapshot for {batch_date} to video with model v2.3", environment
    )
    return {
        "status": "seeded",
        "environment": environment,
        "full_demo": outputs,
        "pending_publish": pending_publish,
        "dashboard_state": get_dashboard_state(environment),
    }


def force_seed_demo_content(environment: str = "test") -> Dict[str, Any]:
    configure_logging()
    clear_environment_data(environment)

    outputs = demo_flow(environment)
    batch_date = datetime.now().strftime("%Y-%m-%d")
    pending_publish = run_assistant(
        f"Publish recommendation snapshot for {batch_date} to video with model v2.3",
        environment,
    )

    return {
        "status": "force_seeded",
        "environment": environment,
        "full_demo": outputs,
        "pending_publish": pending_publish,
        "dashboard_state": get_dashboard_state(environment),
    }


def _read_json(file_path: Path) -> Dict[str, Any]:
    return json.loads(file_path.read_text(encoding="utf-8"))


def _list_recent_records(environment: str, limit: int = 10) -> List[Dict[str, Any]]:
    env_dir = resolve_environment(environment)
    files = sorted(
        [p for p in env_dir.glob("*.json") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]
    records: List[Dict[str, Any]] = []
    for file_path in files:
        payload = _read_json(file_path)
        records.append(
            {
                "filename": file_path.name,
                "tool_name": payload.get("tool_name"),
                "stage": payload.get("stage"),
                "user_approved": payload.get("user_approved"),
                "timestamp_utc": payload.get("timestamp_utc"),
            }
        )
    return records


def _list_pending_releases(environment: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for file_path in sorted(pending_dir(environment).glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        payload = _read_json(file_path)
        items.append(
            {
                "release_id": file_path.stem,
                "environment": payload.get("environment"),
                "tool_name": payload.get("tool_name"),
                "params": payload.get("params", {}),
                "created_at_utc": payload.get("created_at_utc"),
            }
        )
    return items


def _latest_record_by_tool(environment: str, tool_name: str) -> Dict[str, Any] | None:
    env_dir = resolve_environment(environment)
    candidates = sorted(
        env_dir.glob(f"{tool_name}_*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not candidates:
        return None
    return _read_json(candidates[0])


def _read_log_tail(limit: int = 18) -> List[str]:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    return lines[-limit:]


def get_dashboard_state(environment: str) -> Dict[str, Any]:
    inference_record = _latest_record_by_tool(environment, "run_batch_inference")
    publish_record = _latest_record_by_tool(environment, "publish_recommendation_snapshot")

    monitor_summary = {
        "latest_users_scored": None,
        "latest_manual_review_queue": None,
        "age_group_exposure_gap": None,
        "region_exposure_gap": None,
        "diversity_index": None,
        "latest_model_version": None,
        "latest_publication_status": None,
    }

    if inference_record:
        result = inference_record.get("result", {})
        fairness = result.get("fairness_monitor", {})
        monitor_summary.update(
            {
                "latest_users_scored": result.get("estimated_users_scored"),
                "latest_manual_review_queue": result.get("manual_review_queue"),
                "age_group_exposure_gap": fairness.get("age_group_exposure_gap"),
                "region_exposure_gap": fairness.get("region_exposure_gap"),
                "diversity_index": fairness.get("diversity_index"),
                "latest_model_version": result.get("model_version"),
            }
        )

    if publish_record:
        monitor_summary["latest_publication_status"] = publish_record.get("result", {}).get("status")

    return {
        "environment": environment,
        "pending_releases": _list_pending_releases(environment),
        "recent_records": _list_recent_records(environment),
        "monitor_summary": monitor_summary,
        "log_tail": _read_log_tail(),
        "latest_snapshot_preview": _build_recommendation_preview(environment),
    }


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "GovernedEcommerceBatchDemo/1.0"

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

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(INDEX_HTML)
            return

        if parsed.path == "/api/state":
            query = parse_qs(parsed.query)
            environment = query.get("environment", ["test"])[0]
            try:
                if environment == "test":
                    test_state = get_dashboard_state(environment)
                    if not test_state["recent_records"] and not test_state["pending_releases"]:
                        force_seed_demo_content(environment)
                payload = get_dashboard_state(environment)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=400)
                return
            self._send_json(payload)
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            body = self._read_json_body()

            if parsed.path == "/api/run":
                instruction = body["instruction"]
                environment = body.get("environment", "test")
                self._send_json(run_assistant(instruction, environment))
                return

            if parsed.path == "/api/approve":
                release_id = body["release_id"]
                self._send_json(approve_release(release_id))
                return

            if parsed.path == "/api/full_demo":
                environment = body.get("environment", "test")
                result = demo_flow(environment)
                self._send_json({
                    "status": "full_demo_completed",
                    "environment": environment,
                    "result": result,
                    "dashboard_state": get_dashboard_state(environment),
                })
                return

            if parsed.path == "/api/seed":
                environment = body.get("environment", "test")
                self._send_json(force_seed_demo_content(environment))
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
    for environment in ENVIRONMENTS:
        resolve_environment(environment)
        pending_dir(environment)

    test_state = get_dashboard_state("test")
    if not test_state["recent_records"] and not test_state["pending_releases"]:
        force_seed_demo_content("test")

    selected_port = port or find_free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", selected_port), RequestHandler)
    url = f"http://127.0.0.1:{selected_port}"
    print(f"Server running at {url}")
    (BASE_DIR / "last_launch_url.txt").write_text(url, encoding="utf-8")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\nServer stopped.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Governed e-commerce batch recommendation UI demo.")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--demo", action="store_true", help="Run the full flow once and exit.")
    parser.add_argument("--seed", action="store_true", help="Force seed the environment with sample demo artifacts.")
    parser.add_argument("--environment", default="test", choices=["test", "production"])
    parser.add_argument("instruction", nargs="?", help="Optional instruction for CLI mode.")
    parser.add_argument("--approve", help="Approve a pending release by ID.")
    args = parser.parse_args()

    configure_logging()

    if args.seed:
        print(json.dumps(force_seed_demo_content(args.environment), indent=2, ensure_ascii=False))
    elif args.demo:
        print(json.dumps(demo_flow(args.environment), indent=2, ensure_ascii=False))
    elif args.approve:
        print(json.dumps(approve_release(args.approve), indent=2, ensure_ascii=False))
    elif args.instruction:
        print(json.dumps(run_assistant(args.instruction, args.environment), indent=2, ensure_ascii=False))
    else:
        start_server(args.port, open_browser=not args.no_browser)
