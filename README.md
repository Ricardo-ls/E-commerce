# E-commerce

Minimal governed workflow demo for a nightly e-commerce batch recommendation release.

This repository is intentionally small. It is not a recommendation algorithm research project, not a multi-agent system, and not a full backend product. It is a lightweight local demo built to show one clear operational story:

`Generate recommendations -> Preview results -> Request publish -> Approve publish -> Audit trail`

The goal is to make that story easy to explain in a classroom, PPT, portfolio, or live walkthrough.

## 1. Project Positioning

This project has been deliberately narrowed into a **minimum demo for governed batch recommendation delivery**.

It focuses on:

- a single nightly batch snapshot
- a simple publish gate
- explicit human approval before release
- local auditability
- stable demo behavior with minimal setup

It does **not** focus on:

- online serving infrastructure
- recommendation model training
- offline evaluation pipelines
- complex approval queues
- fairness dashboards
- natural language orchestration
- multi-environment platform management

If you need a one-sentence description for presentation use, this is the intended version:

> A minimal Python demo that shows how a nightly e-commerce recommendation batch can be generated, reviewed, approved, published, and audited through a simple governed workflow.

## 2. Demo Story

The entire product story is one small closed loop:

1. Generate a nightly recommendation batch
2. Preview a few sample recommendation rows
3. Request publish
4. Require explicit approval before release
5. Record every action in an audit trail

That is the whole demo.

The point is not to prove recommendation quality. The point is to demonstrate **governance logic around model output**.

## 3. What the UI Shows

The interface is intentionally reduced to four areas:

### Batch Summary

Shows the current batch snapshot at a glance:

- batch date
- model version
- number of users covered
- current publish status

### Recommendation Preview

Shows a few deterministic example recommendation rows so the audience sees concrete output, not just abstract pipeline states.

Each row includes:

- user id
- item id
- placement slot
- score
- short reason

### Publish Control

Shows the workflow gate and what the operator should do next.

Supported states:

- `draft`
- `pending_approval`
- `published`

### Audit Trail

Shows the exact actions taken during the demo, in order.

Typical entries:

- `generate_batch`
- `request_publish`
- `approve_publish`

## 4. Minimal State Model

The backend keeps only three core state objects:

### `batch_snapshot`

Contains the generated recommendation batch metadata and preview rows.

Example fields:

- `batch_date`
- `model_version`
- `users_covered`
- `items_ranked`
- `preview`
- `generated_at_utc`

### `publish_status`

Represents the release gate:

- `draft`
- `pending_approval`
- `published`

### `audit_log`

An append-only list of workflow events, each with:

- UTC timestamp
- action name
- message

This is enough to make the demo understandable while still preserving governance traceability.

## 5. Why This Repo Is Useful

This repository is helpful when you want to demonstrate:

- model outputs should not immediately become user-facing releases
- publishing should pass through an explicit gate
- human approval can be part of a simple ML workflow
- audit trails matter even in small systems
- governance concepts can be shown without building a full platform

It is especially suitable for:

- classroom demos
- portfolio projects
- architecture walkthroughs
- AI governance presentations
- product design discussion for ML operations

## 6. Tech Stack

The project intentionally stays lightweight:

- Python 3.10+
- built-in `http.server`
- local JSON file storage
- local log file
- plain HTML, CSS, and JavaScript embedded in the Python app
- `unittest` for validation

No database is required.

No frontend framework is required.

No external service is required.

## 7. Repository Structure

```text
.
├── app_ecommerce_recommendation_ui.py
├── tools_ecommerce_recommendation.py
├── demo_ecommerce_recommendation_flow.py
├── test_ecommerce_recommendation_demo.py
├── start_ui_demo.sh
├── Launch Demo.command
├── pyproject.toml
├── data/
└── logs/
```

### File roles

`app_ecommerce_recommendation_ui.py`

- main application entry point
- local HTTP server
- embedded demo UI
- state transitions
- API handlers
- state persistence

`tools_ecommerce_recommendation.py`

- deterministic batch snapshot generator
- sample preview row generation

`demo_ecommerce_recommendation_flow.py`

- runs the full minimal demo flow in CLI mode

`test_ecommerce_recommendation_demo.py`

- validates the minimum workflow behavior

`start_ui_demo.sh`

- starts the local demo quickly from the repository root

`Launch Demo.command`

- macOS-friendly launcher that delegates to the shell script

`pyproject.toml`

- minimal project metadata

## 8. Installation

Clone the repository:

```bash
git clone https://github.com/Ricardo-ls/E-commerce.git
cd E-commerce
```

Check your Python version:

```bash
python3 --version
```

Recommended:

- Python 3.10 or newer

This demo uses only the standard library in its main runtime path, so there is no heavy dependency installation step.

## 9. How to Run the UI

Start the application:

```bash
python3 app_ecommerce_recommendation_ui.py
```

Or use the helper script:

```bash
./start_ui_demo.sh
```

On macOS, you can also launch:

```bash
./Launch\ Demo.command
```

The app starts a local server and opens the browser automatically unless disabled.

## 10. How to Use the Demo

The intended click path is:

1. Click `Generate Batch`
2. Look at `Batch Summary`
3. Look at `Recommendation Preview`
4. Click `Request Publish`
5. Observe the status change to `pending_approval`
6. Click `Approve Publish`
7. Observe the status change to `published`
8. Show the `Audit Trail`

This click path is the main deliverable of the repository.

## 11. CLI Workflow

You can also run the state transitions from the command line.

Reset the state:

```bash
python3 app_ecommerce_recommendation_ui.py --reset
```

Generate a batch:

```bash
python3 app_ecommerce_recommendation_ui.py --generate
```

Request publish:

```bash
python3 app_ecommerce_recommendation_ui.py --request-publish
```

Approve publish:

```bash
python3 app_ecommerce_recommendation_ui.py --approve-publish
```

Run the full minimal flow:

```bash
python3 demo_ecommerce_recommendation_flow.py
```

## 12. API Endpoints

The app exposes a very small local API:

### `GET /api/state`

Returns the full current demo state.

### `POST /api/generate`

Creates a fresh recommendation batch snapshot and resets the publish status to `draft`.

### `POST /api/request_publish`

Moves the current batch from `draft` to `pending_approval`.

### `POST /api/approve_publish`

Moves the current batch from `pending_approval` to `published`.

### `POST /api/reset`

Resets the stored demo state back to its empty initial value.

## 13. Local Persistence

This project intentionally uses local files instead of a database.

### State file

The current workflow state is stored in:

```text
data/demo_state.json
```

This file contains:

- current batch snapshot
- current publish status
- audit log history

### Log file

Application logs are written to:

```text
logs/assistant.log
```

This keeps the project simple while still showing traceability.

## 14. Testing

Run the tests with:

```bash
python3 -m unittest -v test_ecommerce_recommendation_demo.py
```

The tests cover the minimum viable governance chain:

- batch generation creates a snapshot
- publish request moves state to `pending_approval`
- approval moves state to `published`
- invalid action order is rejected
- state persists to local JSON

The test suite is intentionally small because the project goal is clarity, not exhaustive platform simulation.

## 15. Presentation Notes

If you are using this repository in a presentation, the recommended explanation order is:

1. Start with the problem: recommendation outputs should not directly go live
2. Show the generated batch
3. Show a few preview rows
4. Show that publish requires a separate action
5. Show that approval is explicit
6. End on the audit trail

That framing helps the audience understand this as a **governed release workflow**, not just a UI mockup.

## 16. Design Principles Behind This Version

This repository was intentionally simplified under the following constraints:

- keep the project lightweight
- use local Python services
- avoid heavy frameworks
- keep storage file-based
- retain audit logging
- prioritize stable demos over advanced architecture
- prefer a clear story over a large feature list

In other words, this version optimizes for comprehension and repeatability.

## 17. Example Success Criteria

This demo is successful when:

- someone can run it locally in minutes
- the main workflow is understandable without explanation-heavy setup
- the UI clearly shows the governance gate
- the audit trail makes the release history visible
- the project feels intentionally scoped rather than unfinished

## 18. Future Extensions

These are possible future extensions, but they are intentionally out of scope for the current version:

- multi-environment support
- richer approval roles
- multiple batch history views
- recommendation quality metrics
- richer monitoring panels
- exportable audit reports
- real database-backed persistence
- separate frontend/backend deployment

For the current repository, keeping those ideas out is part of the design discipline.

## 19. License and Usage

Use this repository as a learning demo, presentation artifact, or prototype starting point.

If you extend it, the clearest path is usually to preserve the core workflow first and only then add surrounding capabilities.

---

If you want to explain the repository in one line on GitHub, use:

**Minimal governed workflow demo for nightly e-commerce batch recommendation publishing.**
