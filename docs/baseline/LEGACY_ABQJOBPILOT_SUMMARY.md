# LEGACY_ABQJOBPILOT_SUMMARY

## 1. Document Metadata

```text
document: LEGACY_ABQJOBPILOT_SUMMARY.md
audit date: 2026-07-26
repository root: D:\Projects\abqjobpilot
repository name: abq_job_pilot / Abaqus Job Pilot
branch: main...origin/main
HEAD commit: aff4cdc59b34a6a472a822860be7a5d3dba2ee1f
working tree: DIRTY before audit; existing modified files plus untracked tests/test_queue_store.py
primary language: Python
package name: abqjobpilot
project version: 0.1.0
report output path: D:\Projects\abqjobpilot\LEGACY_ABQJOBPILOT_SUMMARY.md
files modified: LEGACY_ABQJOBPILOT_SUMMARY.md only during this audit
Abaqus executed: NO
queue worker executed: NO
```

仓库身份证据：`README.md:1-4` 将项目命名为 `Abaqus Job Pilot`；Git remote 指向 `https://github.com/BrunelXian/abq_job_pilot.git`；入口文件为 `run_gui.py:1-5`。版本证据：`abqjobpilot/__init__.py:1-3`。

任务前 working tree：

```text
## main...origin/main
 M abqjobpilot/config.py
 M abqjobpilot/gui_app.py
 M abqjobpilot/parsers.py
 M abqjobpilot/queue_store.py
 M abqjobpilot/runner_core.py
 M abqjobpilot/settings_store.py
 M tests/test_parsers.py
 M tests/test_runner_core.py
?? tests/test_queue_store.py
```

## 2. Executive Summary

AbqJobPilot 的原始目的，是给 Abaqus `.inp` 批量算例提供本地桌面队列、顺序运行和实时日志监控。README 声称它是 standalone desktop tool，并支持 queue execution、datacheck-first、live monitoring、AI-assisted log diagnosis，证据见 `README.md:32-38`。实际代码实现了 Tkinter GUI、JSON 文件队列、Agent Command 白名单解析、Abaqus command list 构造、顺序 runner、`.sta/.log` tail、基本 fatal/success 分类和报告 JSON 写出。最稳定的三项能力是：内部命令解析和白名单拒绝、JSON 队列读写和重复活动任务拒绝、Abaqus command builder 与 datacheck 禁用 GPU 参数。最严重的三项局限是：硬编码仓库/runtime/Abaqus 默认路径、无正式 schema/CLI/API、无 timeout/retry/license/stale artifact/ODB 可读性验证。它不是通用 runtime，也不是多机队列系统；它是一个本地 GUI queue runner 应用，带部分可复用的 Abaqus adapter 能力。它在新 Controlled CAE Runtime 中最合理定位是 `Abaqus Job Lifecycle Adapter` 的 legacy reference，不应作为 runtime 主状态机。总体状态：`USEFUL_LEGACY_ASSET`。

## 3. Original Mission and Scope

### 宣称的使命

文档声称项目用于管理 Abaqus `.inp` job queues，适用于 simulation batches、parameter sweeps、strategy pools 和 long-running research workflows，证据见 `README.md:32-36`。README 还声称支持 batch queue、sequential execution、datacheck-first、safe interruption、live monitoring、result review、Agent-friendly control、resource awareness 和 local output style，证据见 `README.md:40-52`。

### 实际实现范围

实际代码支持 GUI 入口 `run_gui.py:1-5`；启动 GUI 时初始化 storage、创建 `QueueRunner`、定时刷新，证据见 `abqjobpilot/gui_app.py:142-171`。队列使用 JSON 文件，`load_queue()` 会初始化 runtime 并读取 `QUEUE_FILE`，证据见 `abqjobpilot/queue_store.py:16-38`。入队会验证 `.inp` 存在、后缀、CPU、work_dir 和活动重复任务，证据见 `abqjobpilot/queue_store.py:101-136`；保存 job record，证据见 `abqjobpilot/queue_store.py:139-198`。runner 会按 `QUEUED` / `DATACHECK_OK` 顺序领取 job，并调用 `run_next_job()`，证据见 `abqjobpilot/runner_core.py:325-340`。Abaqus 进程启动由 `_run_command()` 使用 `subprocess.Popen(command, cwd=job["work_dir"])` 实现，证据见 `abqjobpilot/runner_core.py:175-200`。

### 明确不支持的内容

| 能力 | 当前状态 | 证据 |
| --- | --- | --- |
| 自动运行 Abaqus | `IMPLEMENTED`，但只在 GUI Start Queue 确认后 | `abqjobpilot/gui_app.py:812-823`, `abqjobpilot/runner_core.py:203-207` |
| 真实队列 | `PARTIAL`，本地 JSON 顺序队列 | `abqjobpilot/queue_store.py:26-38`, `abqjobpilot/runner_core.py:325-340` |
| 多机/远程节点 | `MISSING` | 无 server/client/worker node 代码；文件列表无对应模块 |
| license 调度 | `MISSING` | 仅 README roadmap 提到 finer license classification，`README.md:150-153` |
| 作业取消 | `PARTIAL`，只支持 stop after current 和 skip QUEUED；不能杀当前 Abaqus | `abqjobpilot/runner_core.py:321-323`, `abqjobpilot/gui_app.py:831-843` |
| retry | `MISSING` | 无 retry 状态/函数；状态枚举不含 retry，`abqjobpilot/config.py:18-43` |
| timeout | `MISSING`，runner polling 无超时 | `abqjobpilot/runner_core.py:193-195` |
| 恢复 | `PARTIAL`，`DATACHECK_OK` 可继续 full run；无 crash recovery claim/lease | `abqjobpilot/runner_core.py:228-268` |
| ODB 验证 | `PARTIAL`，只查 size/existence，不打开验证 | `abqjobpilot/runner_core.py:97-104` |
| 安全审批 | `PARTIAL`，GUI messagebox human gate；无 token/ledger | `abqjobpilot/gui_app.py:817-823` |
| 完整 evidence | `PARTIAL`，report JSON 和 manifest，但无 artifact hash/provenance | `abqjobpilot/runner_core.py:152-172` |

## 4. Current Architecture Map

```text
User / GUI
    ↓
run_gui.py → AbqJobPilotApp
    ↓
Add INP / Add Folder / Agent Command
    ↓
queue_store.add_inp_job_to_queue / add_folder_to_queue
    ↓
runtime\queue.json
    ↓
GUI Start Queue confirmation
    ↓
QueueRunner.start → _run_loop → run_next_job
    ↓
build_abaqus_datacheck_command / build_abaqus_full_run_command
    ↓
subprocess.Popen([...], cwd=job["work_dir"])
    ↓
.log stdout/stderr + .sta/.msg/.dat/.odb in INP folder
    ↓
parsers.classify_datacheck_attempt / classify_final_verdict
    ↓
runtime\live_status.json + runtime\reports\*.json + manifest.json
```

不存在或非正式组件：CLI 为 `MISSING`；public API 为 `MISSING`；server/client 为 `MISSING`；multi-node worker 为 `MISSING`；SQLite backend 为 `DOCUMENTED ONLY` roadmap，见 `README.md:150-155`。

主要入口：`run_gui.py:1-5`。核心对象：`AbqJobPilotApp` (`abqjobpilot/gui_app.py:142-171`)、`AgentCommandConsole` (`abqjobpilot/command_console.py:40-53`)、`QueueRunner` (`abqjobpilot/runner_core.py:303-350`)。关键状态对象是普通 dict job record，字段由 `_build_job_record()` 写出，见 `abqjobpilot/queue_store.py:54-98`。外部依赖主要是 Python 标准库和本机 Abaqus command；requirements 声明 MVP 使用标准库，见 `requirements.txt:1`。进程启动位置：Abaqus 在 `abqjobpilot/runner_core.py:183-192`；Windows shutdown 和 taskmgr 在 `abqjobpilot/gui_app.py:690-695`、`abqjobpilot/gui_app.py:762-765`；GPU 查询使用 `subprocess.run(nvidia-smi)`，见 `abqjobpilot/gui_app.py:610-623`。状态存储：`config.py:10-15`。artifact 存储：Abaqus 输出在 `.inp` 目录，README 证据 `README.md:115-131`，代码证据 `abqjobpilot/queue_store.py:65-97`。

## 5. Repository Structure

| Path | Responsibility | Runtime Critical | Evidence |
| ---- | -------------- | ---------------: | -------- |
| `abqjobpilot/` | 主 Python package | Yes | `abqjobpilot/__init__.py:1-3` |
| `abqjobpilot/gui_app.py` | Tkinter GUI、按钮、状态刷新、runner 启动 | Yes | `abqjobpilot/gui_app.py:142-171`, `abqjobpilot/gui_app.py:812-823` |
| `abqjobpilot/command_console.py` | GUI 内 Agent Command Console | Medium | `abqjobpilot/command_console.py:40-53`, `abqjobpilot/command_console.py:147-185` |
| `abqjobpilot/command_parser.py` | 白名单内部命令解析 | Medium | `abqjobpilot/command_parser.py:25-97` |
| `abqjobpilot/queue_store.py` | JSON queue persistence 和 job record | Yes | `abqjobpilot/queue_store.py:16-38`, `abqjobpilot/queue_store.py:54-98` |
| `abqjobpilot/runner_core.py` | Abaqus command builder、runner、report 写出 | Yes | `abqjobpilot/runner_core.py:32-74`, `abqjobpilot/runner_core.py:175-200` |
| `abqjobpilot/parsers.py` | 日志/状态分类 | Yes | `abqjobpilot/parsers.py:8-24`, `abqjobpilot/parsers.py:164-201` |
| `abqjobpilot/monitor.py` | `.sta` 和 console log tail | Medium | `abqjobpilot/monitor.py:10-18` |
| `abqjobpilot/settings_store.py` | GUI settings JSON | Medium | `abqjobpilot/settings_store.py:9-18`, `abqjobpilot/settings_store.py:21-48` |
| `runtime/` | 本地 queue/live/report 状态，git ignored | Yes, runtime local | `.gitignore:15-21`, `abqjobpilot/config.py:10-14` |
| `tests/` | 离线单元测试和 fake INP fixture | Medium | `tests/test_queue_store.py:10-24`, `tests/fixtures/Job_test.inp:2` |
| `run_gui.py` | GUI 启动脚本 | Yes | `run_gui.py:1-5` |
| `README*.md` | 用户文档/roadmap | No | `README.md:32-155` |

## 6. Abaqus Job Lifecycle

| Lifecycle Step | Implementation | Input | Output | Persisted State | Tests | Verdict |
| -------------- | -------------- | ----- | ------ | --------------- | ----- | ------- |
| request | GUI Add INP/Add Folder 或 Agent Command | 文件对话框路径或 internal command | parsed args / path | none before enqueue | parser tests `tests/test_command_parser.py:7-50` | IMPLEMENTED |
| validation | `_validate_new_job()` | `inp_path`, `cpus`, `job_name`, existing jobs | ok/message | none | queue duplicate tests `tests/test_queue_store.py:47-53` | IMPLEMENTED |
| job preparation | `_build_job_record()` | resolved Path, resources, names | dict job record | `queue.json` | queue tests `tests/test_queue_store.py:32-45` | IMPLEMENTED |
| command construction | `build_abaqus_datacheck_command()`, `build_abaqus_full_run_command()` | job dict | `list[str]` command | command later written to `.log` | `tests/test_runner_core.py:12-37` | IMPLEMENTED |
| queue or direct execution | `QueueRunner._next_queued_job()` | `queue.json` jobs | first queued job | live status writes | no worker execution test | PARTIAL |
| process start | `_run_command()` | command list + `work_dir` | return code | `.log`, `live_status.json` | no Popen mock test | PARTIAL |
| status monitoring | `_write_live_status()` polls `.sta` and ODB size | job paths | JSON telemetry | `live_status.json` | parser tests only | PARTIAL |
| completion/failure classification | `classify_datacheck_attempt()`, `classify_final_verdict()` | `.log/.sta/.msg/.dat`, return code | verdict dict | queue updates/report | parser tests `tests/test_parsers.py:7-49` | IMPLEMENTED for patterns; PARTIAL physically |
| artifact collection | `_refresh_job_paths()`, `_odb_size()` | work_dir + job_name | path fields, ODB size | queue/report JSON | no freshness/readability test | PARTIAL |
| report | `_write_report()` | final job dict | per-job JSON + manifest | `runtime/reports` | no report test | PARTIAL |

绕过风险：`run_next_job(job)` 是 public module-level function，调用即提交 Abaqus，docstring 明确说明，见 `abqjobpilot/runner_core.py:203-207`。恢复支持有限：`DATACHECK_OK` 可直接进入 full run，见 `abqjobpilot/runner_core.py:228-268`；没有 worker lease、claim id、stale lock 或 crash recovery。

## 7. Command Construction and Process Execution

Abaqus executable 来源：`settings_store.load_settings()` 的 `abaqus_cmd` 优先，否则 `config.ABAQUS_CMD`，见 `abqjobpilot/runner_core.py:32-39` 和 `abqjobpilot/settings_store.py:9-18`。默认 Abaqus 路径硬编码为 `D:\ABAQUS2024\Commands\abq2024.bat`，见 `abqjobpilot/config.py:5`。command 使用固定 list 组装；`.bat/.cmd` 通过 `["cmd.exe", "/c", abaqus_cmd]`，避免 `shell=True`，见 `abqjobpilot/runner_core.py:32-39`。working directory 来自 job record 的 `work_dir`，见 `abqjobpilot/runner_core.py:183-185`。job name 和 input file 来自 job dict，见 `abqjobpilot/runner_core.py:65-74`。CPU 通过 `max(1, int(...))` 下限保护，但无上限 policy，见 `abqjobpilot/runner_core.py:25-29`。timeout 不存在，poll loop 等到 `process.poll()` 非空，见 `abqjobpilot/runner_core.py:193-195`。stdout/stderr 写入 `.log`，见 `abqjobpilot/runner_core.py:179-188`。return code 写入 log/live status，并参与 verdict，见 `abqjobpilot/runner_core.py:196-199`, `abqjobpilot/runner_core.py:233-273`。未验证 Abaqus executable 是否存在，也未 probe Abaqus 版本。

| Process Entry | Caller | Command Source | CWD Source | shell | Guard | Bypass Risk |
| ------------- | ------ | -------------- | ---------- | ----: | ----- | ----------- |
| `subprocess.Popen(command, ...)` in `_run_command` | `run_next_job()` | `build_abaqus_*_command()` | `job["work_dir"]` | False/implicit | GUI confirmation only if through GUI | HIGH: module function can be called directly |
| `subprocess.run(["nvidia-smi", ...])` | GUI resource panel | fixed list | inherited | False/implicit | timeout 1.5s | LOW |
| `subprocess.Popen(["shutdown", ...])` | GUI auto shutdown | fixed list | inherited | False/implicit | settings + idle check | MEDIUM Windows side effect |
| `subprocess.Popen(["taskmgr.exe"])` | GUI button | fixed list | inherited | False/implicit | user click | LOW |
| `os.startfile(path)` | Open Work Folder | selected job `work_dir` | n/a | n/a | path exists check | LOW |

没有发现 public raw shell launcher；Agent Command parser 明确拒绝未知命令，见 `abqjobpilot/command_parser.py:25-97` 和 `tests/test_command_parser.py:35-37`。

## 8. Queue and Scheduling Model

队列模型是本地 JSON 文件队列，不是数据库/外部调度器。`load_queue()` 读取 `QUEUE_FILE`，`save_queue()` 写整个 list，见 `abqjobpilot/queue_store.py:26-38`。queue item schema 是普通 dict，无 version 字段，由 `_build_job_record()` 生成，见 `abqjobpilot/queue_store.py:54-98`。状态枚举在 `config.py:18-43`。worker 是 `QueueRunner` 的单线程 daemon，见 `abqjobpilot/runner_core.py:303-350`。不支持并发；无文件锁；无 stale job 检测；无 retry；无优先级；资源限制只有 CPU/GPU 字段传参，无全局 resource scheduler；取消只有 skip QUEUED 和 stop-after-current；无 pause；恢复只对 `DATACHECK_OK` 有有限语义；重复活动任务按 `inp_path` 或 `job_name + work_dir` 拒绝，见 `abqjobpilot/queue_store.py:111-136`；无 dead-letter/quarantine；无 runner node/claim id；无 license awareness。

真实状态图：

```text
QUEUED
→ DATACHECK_RUNNING
→ DATACHECK_OK
→ FULL_RUNNING
→ COMPLETED_OK / COMPLETED_WITH_WARNINGS

QUEUED / DATACHECK_RUNNING / FULL_RUNNING
→ DATACHECK_FAILED / DATACHECK_FAILED_INVALID_GPU_OPTION / FAILED_FATAL / UNKNOWN_INTERRUPTED

QUEUED
→ SKIPPED

CANCELLED exists in config but no current-job kill implementation found.
```

证据：状态枚举 `abqjobpilot/config.py:18-43`；runner transitions `abqjobpilot/runner_core.py:230-288`；skip implementation `abqjobpilot/queue_store.py:259-272`。

## 9. Job Monitoring and Diagnosis

读取能力：

| File / Signal | Read? | Evidence | Limitation |
| --- | --- | --- | --- |
| `.sta` | Yes | `abqjobpilot/runner_core.py:269`, `abqjobpilot/monitor.py:10-11` | 只解析 numeric tail 和 success/fatal text |
| `.msg` | Yes | `abqjobpilot/runner_core.py:270` | 只做 pattern search |
| `.dat` | Yes | `abqjobpilot/runner_core.py:271` | 只做 pattern search |
| `.log` | Yes | `abqjobpilot/runner_core.py:234`, `abqjobpilot/runner_core.py:272`, `abqjobpilot/monitor.py:14-18` | append 模式，需 latest attempt 规避旧错误 |
| `.odb` | Existence/size only | `abqjobpilot/runner_core.py:97-104` | 不打开、不验证 freshness/readability |
| `.lck` | No first-class read | `.gitignore:39` only ignores; no parser path | stale lock MISSING |
| return code | Yes | `abqjobpilot/runner_core.py:196-199`, `abqjobpilot/parsers.py:147-154`, `abqjobpilot/parsers.py:182-188` | 无 timeout 区分 |

完成判定：`SUCCESS_PATTERN = "THE ANALYSIS HAS COMPLETED SUCCESSFULLY"`，见 `abqjobpilot/parsers.py:8`；成功返回 `COMPLETED_OK` 或 `COMPLETED_WITH_WARNINGS`，见 `abqjobpilot/parsers.py:189-195`。失败判定：fatal patterns 包括 terminated、aborted、too many attempts、input processor error、Abaqus Error、Error in job，见 `abqjobpilot/parsers.py:9-17`。非 fatal 排除 CONTACT FORCE ERROR TOLERANCE 等，见 `abqjobpilot/parsers.py:18-23` 和测试 `tests/test_parsers.py:7-10`。datacheck 会读取最新 attempt block，避免旧失败污染当前判定，见 `abqjobpilot/parsers.py:87-103` 和测试 `tests/test_parsers.py:22-39`。

必须区分：

```text
process completion: process.poll()/returncode; IMPLEMENTED
solver completion: text patterns; PARTIAL
artifact existence: ODB size/existence; PARTIAL
artifact validity: ODB readability/freshness/job identity; MISSING
physical validity: MISSING
```

## 10. Configuration and Environment Model

配置来源：`config.py` 硬编码默认值，`settings_store.py` 读取 `runtime/settings.json` 覆盖 GUI defaults。证据：`abqjobpilot/config.py:5-16`，`abqjobpilot/settings_store.py:9-48`。Abaqus 路径默认硬编码，但 GUI Settings 可保存本机路径，见 `abqjobpilot/gui_app.py:76-80`, `abqjobpilot/gui_app.py:113-126`。CPU 默认 14，GPU 默认 0，见 `abqjobpilot/config.py:6-9`。工作目录来自 `.inp` parent，见 `abqjobpilot/queue_store.py:65-69`。环境变量未显式管理。Windows 特定行为包括 `.bat` 通过 `cmd.exe /c`、hidden window flags、`ctypes` system metrics、shutdown、taskmgr，证据见 `abqjobpilot/runner_core.py:32-52` 和 `abqjobpilot/gui_app.py:5-11`, `abqjobpilot/gui_app.py:635-695`。README 声称 Python 3.9+ 和 Windows，见 `README.md:10-15`。requirements 无第三方依赖，见 `requirements.txt:1`。

迁移时必须消除的隐式状态：硬编码 `D:\Projects\abqjobpilot` runtime，见 `abqjobpilot/config.py:10-15`；硬编码 Abaqus 默认路径，见 `abqjobpilot/config.py:5`；直接读取当前真实 `runtime/*.json`；job record 中原地输出到 `.inp` 文件夹；append `.log` 可能含旧 attempt；无 schema version；Windows-only shutdown/taskmgr/ctypes。

## 11. CLI, GUI and User Workflow

### CLI

没有独立 CLI。唯一命令行入口是 `python run_gui.py`，见 `run_gui.py:1-5`。`command_parser.py` 使用 argparse，但它是 GUI Agent Command 的内部 parser，不是 shell CLI，证据见 `abqjobpilot/command_parser.py:48-97`。没有 JSON 输出、稳定 exit code 或 package entry points；`abqjobpilot/api` 目录不存在。CLI verdict：`MISSING`。

### GUI

GUI 使用 Tkinter/ttk，证据见 `abqjobpilot/gui_app.py:8-11`。它能添加 INP、添加文件夹、打开 settings、打开 Agent Console、Start Queue、Stop After Current、Skip Selected、Clear Result、Open Work Folder、Copy log for AI、显示资源信息。真实执行按钮：Add INP 调 `add_inp_job_to_queue()`，见 `abqjobpilot/gui_app.py:714-730`；Add Folder 调 `add_folder_to_queue()`，见 `abqjobpilot/gui_app.py:732-746`；Start Queue 经确认后调 `runner.start()`，见 `abqjobpilot/gui_app.py:812-823`；Stop After Current 调 runner flag，见 `abqjobpilot/gui_app.py:831-833`；Skip 只标记 `QUEUED`，见 `abqjobpilot/gui_app.py:835-843`；Clear Result 只删 queue history，不删 Abaqus 文件，见 `abqjobpilot/gui_app.py:850-880`。GUI 与后台逻辑耦合较强：GUI 直接 import queue_store、runner_core、settings_store，见 `abqjobpilot/gui_app.py:13-26`。

### 推荐的 Legacy 定位

保留 GUI 作为 legacy operator tool 和参考交互，不应迁移为新 runtime 的核心。Agent Command parser 可以迁移为 compatibility adapter；GUI 的 shutdown/taskmgr/resource UI 不应进入 Controlled CAE Runtime 核心。

## 12. Data Contracts and Schemas

| Contract | Format | Versioned | Validated | Persisted | Migration Value |
| -------- | ------ | --------: | --------: | --------: | --------------- |
| job request | argparse namespace / GUI args / ordinary dict | No | Partial | No before enqueue | Medium |
| queue item | ordinary dict JSON | No | Partial | Yes, `queue.json` | High after schema refactor |
| job status | string enum + dict fields | No | Partial | Yes | High |
| execution result | ordinary dict | No | Partial | Partly report JSON | Medium |
| monitor result | ordinary dict/live JSON | No | Partial | Yes `live_status.json` | Medium |
| artifact record | path fields in job dict | No | No freshness/readability | Yes | Medium |
| report | per-job JSON + manifest | No | No | Yes | Medium |
| approval | GUI messagebox only | No | Human only | No ledger | Low |
| configuration | Python constants + settings JSON | No | Partial coercion | Yes | Medium |

项目未使用 dataclass、Pydantic 或 TypedDict。queue item 字段来自普通 dict，见 `abqjobpilot/queue_store.py:70-98`。JSON 写入通过 `utils.write_json()`，见 `abqjobpilot/utils.py:43-64`。

## 13. Safety and Authorization

| Safety Mechanism | Documented Policy | Prompt-level | GUI-level | Programmatic | Tested |
| --- | --- | --- | --- | --- | --- |
| dry-run | No | No | No | No | No |
| approval token | No | No | No | No | No |
| human gate | README says Start Queue required | No | Yes | Partial | No GUI test |
| command allow-list | Yes `README.md:135-140` | No | Yes | Yes parser | Yes `tests/test_command_parser.py:35-37` |
| workspace guard | No | No | No | No | No |
| immutable source | No | No | No | No | No |
| path validation | No formal policy | No | N/A | `.inp` exists/suffix/work_dir | Partial tests |
| CPU limit | No | No | Settings UI | lower bound only, no max runtime policy | command tests |
| timeout | No | No | No | No for Abaqus | No |
| single-use authorization | No | No | No | No | No |
| revocation | No | No | No | No | No |
| audit ledger | No | No | No | report JSON only | No |
| secret protection | `.gitignore` excludes runtime/outputs, not secrets policy | No | No | No | No |

Agent Command 不执行 arbitrary shell 的实现证据是 `SUPPORTED_COMMANDS` 和 unknown rejection，见 `abqjobpilot/command_parser.py:25-97`；测试证据 `tests/test_command_parser.py:35-37`。runner 避免 `shell=True` 是实现层事实，但 `.bat` 仍经 `cmd.exe /c` 执行指定 bat 文件，见 `abqjobpilot/runner_core.py:32-39`。

## 14. Testing and Validation

测试体系：4 个 unittest 文件，16 个测试。覆盖 command parser、log parsers、queue_store 临时 runtime、runner command builder/hidden window options。无真实 Abaqus 测试；无 subprocess Popen mock 测试；无 GUI 自动化测试；无 integration test；无恢复/并发/错误注入/stale artifact/license/ODB readability 测试。

| Command | Exit Code | Result | Notes |
| ------- | --------: | ------ | ----- |
| `python -m unittest discover -s tests -v` | 0 | 16 tests OK | 静态确认测试不调用 `QueueRunner.start()` / `run_next_job()` / `_run_command()` 后执行 |

测试验证代码逻辑，不验证真实物理成功。fixture 是 fake INP，见 `tests/fixtures/Job_test.inp:2`；不能视为 Abaqus 求解 evidence。测试可产生临时 queue，但 `tests/test_queue_store.py:10-30` 保存并恢复 config 到 temp runtime。没有针对绕过 `run_next_job()` 的测试；没有 stale artifact 测试。

## 15. Stable and Reusable Assets

| Asset | Path | Current responsibility | Evidence | Why reusable | Migration prerequisites | Risk |
| --- | --- | --- | --- | --- | --- | --- |
| Agent command parser | `abqjobpilot/command_parser.py` | 白名单解析 enqueue/list/help | `abqjobpilot/command_parser.py:25-97`, tests | 可作为 legacy command compatibility | 分离 GUI、输出 JSON | Low |
| Queue record builder/validation | `abqjobpilot/queue_store.py` | 建 job dict、验证路径/重复 | `abqjobpilot/queue_store.py:54-136` | 字段贴近 Abaqus lifecycle | dataclass/schema/version/idempotency | Medium |
| Abaqus command builder | `abqjobpilot/runner_core.py` | datacheck/full command list | `abqjobpilot/runner_core.py:55-74`, tests | 核心 adapter 能力 | 注入 executable/version/resource policy | Medium |
| Datacheck GPU exclusion | `runner_core.py` | datacheck 不传 gpus | `abqjobpilot/runner_core.py:65-68`, `tests/test_runner_core.py:26-37` | 已知 Abaqus constraint | 保持测试 | Low |
| Latest attempt block parser | `parsers.py` | 避免旧失败污染新 attempt | `abqjobpilot/parsers.py:87-129`, `tests/test_parsers.py:22-39` | 真实问题修复 | 修复 mojibake/增加 phase model | Medium |
| Fatal/success classifier | `parsers.py` | 基本文本分类 | `abqjobpilot/parsers.py:8-24`, `abqjobpilot/parsers.py:164-201` | 可迁移到 diagnostics | 增加 structured rules/evidence spans | Medium |
| JSON atomic writer | `utils.py` | retry + temp replace | `abqjobpilot/utils.py:43-64` | 轻量可复用 | 加文件锁/schema/version | Medium |

## 16. Technical Debt and Known Limitations

| Issue | Severity | Evidence / Explanation |
| --- | --- | --- |
| 硬编码路径 | HIGH | `abqjobpilot/config.py:5-15` |
| 无正式 CLI/API | HIGH | `abqjobpilot/api` 不存在；只有 `run_gui.py:1-5` |
| 普通 dict 无 schema/version | HIGH | queue record `abqjobpilot/queue_store.py:70-98` |
| `run_next_job()` 可被直接调用提交 Abaqus | HIGH | `abqjobpilot/runner_core.py:203-207` |
| 无 Abaqus timeout | HIGH | poll loop `abqjobpilot/runner_core.py:193-195` |
| 无 file lock / worker lease | HIGH | `save_queue()` 整体写 JSON，`abqjobpilot/queue_store.py:36-38` |
| 无 idempotency/provenance/hash | HIGH | queue_id timestamp only `abqjobpilot/queue_store.py:41-43` |
| 旧 artifact 碰撞风险 | HIGH | 输出固定在 INP 文件夹同名 stem，`abqjobpilot/queue_store.py:65-97` |
| 无 ODB freshness/readability 验证 | HIGH | 只 stat size，`abqjobpilot/runner_core.py:97-104` |
| 无 license awareness | MEDIUM | README roadmap 才提到 finer license classification，`README.md:150-153` |
| GUI/后台耦合 | MEDIUM | GUI 直接 import runner/queue，`abqjobpilot/gui_app.py:13-26` |
| Windows-only 行为 | MEDIUM | `ctypes`, shutdown, taskmgr，`abqjobpilot/gui_app.py:5-11`, `abqjobpilot/gui_app.py:682-765` |
| 报告与实际 evidence 薄弱 | MEDIUM | `_write_report()` 写 job dict，无 artifact hash，`abqjobpilot/runner_core.py:152-172` |
| fixture 可能被误解为真实求解 | LOW | fake INP fixture，`tests/fixtures/Job_test.inp:2` |
| 文本编码/中文乱码 | LOW | GUI text 出现 mojibake，如 `abqjobpilot/gui_app.py:759-760` |

## 17. Migration Matrix

| Component | Current Path | Decision | Reason | Target Location | Required Tests |
| --------- | ------------ | -------- | ------ | --------------- | -------------- |
| Command builder | `abqjobpilot/runner_core.py` | REFACTOR | 有价值但需注入 Context/Executor，不可直接提交 | `adapters/abaqus/job/` | command list, no shell, datacheck no gpus, executable validation |
| Status parser | `abqjobpilot/parsers.py` | REFACTOR | 规则可用但需 evidence spans/schema | `adapters/abaqus/diagnostics/` | fatal/success/latest-attempt/stale-log tests |
| Queue item fields | `abqjobpilot/queue_store.py` | REFACTOR | 字段有价值，但普通 dict 无 schema | `interfaces/` + `adapters/abaqus/job/` | schema validation/migration/idempotency |
| Local JSON queue | `abqjobpilot/queue_store.py` | REPLACE | 无锁、无 lease、无并发/恢复 | `runtime/queue/` | claim/lease/retry/stale tests |
| Runner execution loop | `abqjobpilot/runner_core.py` | REFACTOR | 顺序 lifecycle 有价值，但需 Controlled Executor | `runtime/executor/` + adapter | timeout/cancel/recovery tests |
| Agent command parser | `abqjobpilot/command_parser.py` | KEEP | 白名单清晰，适合 legacy compatibility | `legacy/abqjobpilot_command/` | parse/reject tests |
| Tkinter GUI | `abqjobpilot/gui_app.py` | DO NOT MIGRATE | Legacy operator UI；不应进 runtime core | `legacy/gui/` only if needed | smoke import only |
| Auto shutdown / taskmgr | `abqjobpilot/gui_app.py` | DO NOT MIGRATE | 与 CAE runtime 无关，Windows side effect | none | none |
| Monitor tail helpers | `abqjobpilot/monitor.py` | KEEP | 简单 read-only helper | `adapters/abaqus/monitoring/` | missing file/tail tests |
| Settings store | `abqjobpilot/settings_store.py` | REPLACE | 本地 GUI config，不适合 runtime context | `runtime/config/` | precedence/validation tests |
| README claims | `README.md` | DO NOT MIGRATE | 宣传/roadmap 不等于能力 | `legacy/docs/` | none |
| Tests | `tests/` | REFACTOR | 可保留核心单元逻辑，扩展 coverage | corresponding packages | no-execution safety tests |

## 18. Proposed Role in the New Runtime

AbqJobPilot 在新项目中应定位为：

```text
Abaqus Job Lifecycle Adapter
```

建议边界：它可以负责 Abaqus command construction、job preparation、job submission adapter、queue adapter、process/status monitoring、`.sta/.msg/.dat/.lck` diagnosis、adapter-specific artifact discovery。它不应负责全局 Context、通用 Workspace 权限、全局 authorization、Tool Registry、LLM planner、跨求解器 Session、final evidence authority、通用 physics verdict 或 Runtime 主状态机。

代码实际情况支持“作为 adapter reference”，但不支持“直接作为新 Runtime dependency”：原因是 runner 直接 `Popen`，状态是无 schema JSON，配置硬编码，本地 GUI 和后台耦合，缺少 timeout/lease/evidence，证据分别见 `abqjobpilot/runner_core.py:175-200`、`abqjobpilot/queue_store.py:54-98`、`abqjobpilot/config.py:5-15`、`abqjobpilot/gui_app.py:13-26`。

## 19. Recommended Extraction Order

```text
Batch 1: status and command data contracts
```

输入：`queue_store._build_job_record()` 字段、`config.STATUS_VALUES`。输出：versioned dataclasses/schema。依赖：无真实 Abaqus。风险：历史 JSON 兼容。验收：schema validation、migration tests。是否需要真实 Abaqus：No。

```text
Batch 2: pure command builder
```

输入：`build_abaqus_datacheck_command()`、`build_abaqus_full_run_command()`。输出：pure `AbaqusCommandPlan`。依赖：runtime config/executable policy。风险：`.bat` handling。验收：no shell, cwd, datacheck no gpus, executable missing tests。是否需要真实 Abaqus：No。

```text
Batch 3: monitor and log diagnosis
```

输入：`parsers.py`、`monitor.py`。输出：diagnostic result with evidence spans。依赖：artifact locator。风险：旧日志污染、encoding。验收：latest attempt, fatal exclusions, stale artifact tests。是否需要真实 Abaqus：No。

```text
Batch 4: queue adapter
```

输入：legacy queue semantics。输出：Controlled queue adapter with claim/lease/idempotency。依赖：runtime state store。风险：crash recovery。验收：concurrent claim, retry, stale lock tests。是否需要真实 Abaqus：No。

```text
Batch 5: controlled execution integration
```

输入：command plan + executor。输出：controlled subprocess execution with timeout/cancel/evidence. 依赖：authorization/workspace/executor。风险：真实 side effects。验收：mock subprocess first；later controlled Abaqus integration. 是否需要真实 Abaqus：Only final integration stage。

```text
Batch 6: legacy CLI compatibility
```

输入：Agent Command parser。输出：optional compatibility CLI/API that only produces request objects by default。依赖：contracts。风险：用户误以为 shell。验收：dry-run default, JSON exit codes, reject unsafe submit。是否需要真实 Abaqus：No。

## 20. Final Legacy Verdict

1. AbqJobPilot 的核心价值：把本地 Abaqus `.inp` 批处理从人工接力提交变成本地 JSON 队列、顺序 runner、实时日志监控和基本诊断。
2. 它目前是应用加队列工具，不是通用 runtime；成熟度是 useful legacy asset。
3. 最值得迁移的三项能力：Abaqus command builder；`.sta/.log/.msg/.dat` parser/classifier；queue item/job lifecycle 字段。
4. 必须废弃的三项设计：硬编码路径/本地 runtime；GUI 直接控制 execution；无 schema/lease/timeout/evidence 的 JSON queue。
5. 不建议继续在旧仓库做大型架构开发；只应维护 bugfix 或作为 legacy operator tool。
6. 不适合作为新 Runtime 的直接依赖。
7. 更适合 selective code extraction + adapter 重构；不是整体复制。
8. 新架构正式定位：`Abaqus Job Lifecycle Adapter`。

```text
legacy project: Abaqus Job Pilot
legacy repository: D:\Projects\abqjobpilot / BrunelXian/abq_job_pilot
legacy branch: main
legacy commit: aff4cdc59b34a6a472a822860be7a5d3dba2ee1f
overall maturity: USEFUL_LEGACY_ASSET
recommended status: selective migration reference
recommended new role: Abaqus Job Lifecycle Adapter
continue legacy development: maintenance only, no large runtime architecture work
direct dependency recommended: NO
migration strategy: extract/refactor selected modules behind new Controlled CAE Runtime contracts
top reusable assets: command builder; parser/classifier; queue/job field model; tail helpers; parser tests
top refactor targets: queue_store schema; runner_core executor boundary; parser evidence model
top rejected legacy patterns: hardcoded paths; GUI-driven execution; unversioned dict JSON queue; no timeout/lease/evidence
tests executed: python -m unittest discover -s tests -v
tests passed: 16
tests failed: 0
tests blocked: 0
files modified: LEGACY_ABQJOBPILOT_SUMMARY.md only
final verdict: USEFUL_LEGACY_ASSET_FOR_SELECTIVE_MIGRATION
```

## Final Audit Safety Confirmation

```text
除本报告外没有修改任何文件: YES, intended
没有运行 Abaqus: YES
没有启动 queue worker: YES
没有创建 commit: YES
working tree 与任务前状态一致: YES except this newly added report file
报告位于指定输出路径: D:\Projects\abqjobpilot\LEGACY_ABQJOBPILOT_SUMMARY.md
```
