# Governed E-commerce Batch Recommendation Demo

这是一个围绕“电商夜间批量推荐”场景搭建的本地可演示原型。项目重点不是模型精度，而是把一条**可治理、可审计、可留痕、带审批门禁、带环境隔离**的 batch recommendation 执行链路完整展示出来。

它适合做下面这些事情：

- 演示自然语言如何触发批量推荐流程
- 演示 test / production 环境隔离
- 演示用户可见发布前的审批门禁
- 演示 JSON 审计记录与日志追踪
- 演示一个能直接打开浏览器观看的本地 UI

## 项目核心目标

这个 demo 想表达的不是“推荐分数多高”，而是下面这一整套治理化执行链路：

1. 自然语言输入
2. 意图识别
3. 工具选择
4. 分阶段执行
5. 用户可见发布前审批
6. test / production 环境隔离
7. 审计记录落盘
8. 日志追踪
9. UI 可展示监控摘要、审批队列和样例推荐结果

## 业务背景

场景设定为一个大规模电商平台的夜间低峰批量推荐流程：

1. 平台在夜间收集大量用户行为数据
2. 对数据进行校验、匿名化和最小化处理
3. 调用训练好的推荐模型执行 batch inference
4. 生成推荐结果快照并存储
5. 面向首页、视频流等用户可见 surface 的发布不是自动上线，而是进入审批门禁
6. 人工批准后才完成用户可见发布
7. 全过程保留审计记录、日志和监控摘要

## 项目结构

- `app_ecommerce_recommendation_ui.py`
  - 主程序
  - 本地 HTTP 服务
  - HTML UI
  - 前端交互逻辑
  - 后端 API
  - 自然语言分类
  - 审批机制
  - dashboard state 聚合
  - 自动 seed 测试数据

- `tools_ecommerce_recommendation.py`
  - 工具注册表
  - 各阶段工具函数定义
  - 推荐、存储、发布、审计等阶段的业务返回值

- `test_ecommerce_recommendation_demo.py`
  - 演示测试
  - 验证 seed 后 dashboard 是否非空
  - 验证推荐样例是否可展示
  - 验证 inference 结果字段是否满足 dashboard 聚合

- `demo_ecommerce_recommendation_flow.py`
  - CLI 方式跑一遍完整 demo

- `start_ui_demo.sh`
  - 一键启动 UI

## 当前 pipeline 阶段

项目把推荐流程拆成了多个 stage：

1. `collect_behavior_batch`
   - 收集夜间行为批次

2. `validate_and_prepare_batch`
   - 做数据校验、匿名化、最小化处理等准备工作

3. `run_batch_inference`
   - 执行推荐批量推理
   - 输出监控摘要字段，例如：
     - `estimated_users_scored`
     - `manual_review_queue`
     - `fairness_monitor`
     - `model_version`

4. `store_recommendation_snapshot`
   - 将推荐结果快照存入目标存储

5. `publish_recommendation_snapshot`
   - 用户可见发布阶段
   - 先进入 `blocked_pending_approval`
   - 生成 `pending release`
   - 等待人工批准后才真正执行

6. `inspect_audit_summary`
   - 查看审计摘要

## UI 功能

打开页面后，你会看到以下内容：

- 顶部环境选择：`test` / `production`
- 顶部操作按钮：
  - `Generate Test Data`
  - `Run Full Nightly Job`
  - `Refresh State`
- 指标卡片：
  - Recent records
  - Pending approvals
  - Latest users scored
  - Manual review queue
- Natural-language command center
- Pending release approvals
- Monitoring summary
- Recent audit artifacts
- Recent log tail
- Latest recommendation preview

其中 `Latest recommendation preview` 是为了让页面不只是展示抽象统计，还能直接看到几条样例推荐结果，方便演示。

## 后端 API

项目提供了几个简单的本地 API：

- `GET /`
  - 返回 UI 页面

- `GET /api/state?environment=test|production`
  - 返回 dashboard state
  - 包括：
    - `pending_releases`
    - `recent_records`
    - `monitor_summary`
    - `log_tail`
    - `latest_snapshot_preview`

- `POST /api/run`
  - 执行自然语言指令

- `POST /api/approve`
  - 批准某个 pending release

- `POST /api/full_demo`
  - 跑完整 nightly job demo

- `POST /api/seed`
  - 强制生成测试数据

## 自然语言示例

系统会通过 `classify_instruction()` 把自然语言映射到不同阶段工具，例如：

- `Collect nightly behavior batch for 2026-04-15`
  - 对应 `collect_behavior_batch`

- `Validate and prepare batch for 2026-04-15`
  - 对应 `validate_and_prepare_batch`

- `Run recommendation inference for 2026-04-15 with model v2.3`
  - 对应 `run_batch_inference`

- `Store recommendation snapshot for 2026-04-15 with model v2.3`
  - 对应 `store_recommendation_snapshot`

- `Publish recommendation snapshot for 2026-04-15 to homepage with model v2.3`
  - 对应 `publish_recommendation_snapshot`
  - 需要审批

- `Inspect audit summary for 2026-04-15`
  - 对应 `inspect_audit_summary`

## 数据与留痕

项目的数据和审计结果会落到本地文件系统：

- `data/test/`
- `data/production/`
- `data/<env>/pending_releases/`
- `logs/assistant.log`

每个阶段都会写 JSON artifact，避免只停留在内存里。

另外，记录文件名使用带微秒的时间戳，避免同一秒多阶段执行时互相覆盖。

## 测试流程

项目已经补了一套能直接演示的测试，建议这样看：

```bash
python3 -m unittest -v test_ecommerce_recommendation_demo.py
```

测试覆盖了：

- `force_seed_demo_content("test")` 后 dashboard 是否非空
- `run_batch_inference` 的结果是否包含 dashboard 需要的字段
- 推荐预览是否能从最新推理结果中构造出来
- 空环境是否能被自动补种

## 启动方式

### 方式 1：一键启动 UI

```bash
./start_ui_demo.sh
```

这个脚本会先 seed 一份 `test` 环境数据，然后启动本地 UI。

### 方式 2：直接启动主程序

```bash
python3 app_ecommerce_recommendation_ui.py
```

### 方式 3：CLI 演示

```bash
python3 app_ecommerce_recommendation_ui.py "Run recommendation inference for 2026-04-15 with model v2.3" --environment test
python3 app_ecommerce_recommendation_ui.py "Publish recommendation snapshot for 2026-04-15 to homepage with model v2.3" --environment test
python3 app_ecommerce_recommendation_ui.py --approve <release_id>
python3 app_ecommerce_recommendation_ui.py --demo --environment test
python3 app_ecommerce_recommendation_ui.py --seed --environment test
```

## 演示建议

如果你要现场讲这个项目，我建议按下面顺序：

1. 打开 UI
2. 切到 `test`
3. 点击 `Generate Test Data`
4. 观察：
   - recent records
   - pending approvals
   - monitoring summary
   - log tail
   - latest recommendation preview
5. 再点 `Run Full Nightly Job`
6. 进入 `Pending release approvals`
7. 点击 `Approve publish`
8. 展示审批后的 `latest publication status`

## 这个项目和普通推荐 demo 的区别

普通推荐 demo 往往只展示模型输出或一个结果表。

这个项目更强调的是：

- 执行链路是分阶段的
- 用户可见发布必须经过审批
- test / production 严格隔离
- 每个动作都留下可审计痕迹
- UI 不只是展示结果，也展示治理过程

如果你想把它讲成一句话，可以这样说：

> 这是一个面向电商夜间批量推荐场景的 governed batch inference demo，重点展示自然语言控制、审批门禁、环境隔离、审计留痕和可视化监控。

## 本地目录说明

- `data/test/`
  - 测试环境 JSON 记录

- `data/production/`
  - 生产环境 JSON 记录

- `data/<env>/pending_releases/`
  - 待审批发布项

- `logs/assistant.log`
  - 运行日志

## 备注

这个项目保持了比较轻量的实现方式：

- 后端使用 Python 标准库
- UI 通过内嵌 HTML/JS 提供
- 数据通过文件系统落盘
- 审计通过 JSON artifact 留痕

所以它适合本地演示、架构展示和治理链路说明，不适合直接当作生产系统模板照搬。
