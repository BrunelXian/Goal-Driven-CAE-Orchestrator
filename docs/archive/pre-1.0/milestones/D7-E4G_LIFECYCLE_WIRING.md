# D7-E4-G — Minimal Owner Lifecycle Acceptance Wiring

2026-11-02 · **OFFLINE_WIRING_READY_FOR_REVIEW / REAL_NOT_RUN**

本轮只新增独立验收接线、对应离线测试、冻结 Manifest 和本文；AF 生产 API、F2 源码及失败报告未改。原 `BLOCKED_HOST_PROBE / CONSOLE_JOB_MEMBERSHIP`、旧 UNKNOWN 全部保留。新有限口径为 `e4g-supervised-session-test-only-v1`：受监督会话内的精确 Owner 启停，不保证跨 GUI、Owner、Job 或 Windows 会话退出存活。

## 来源与实际绑定

冻结对象在同目录 `D7-E4G_ACCEPTANCE_MANIFEST.json`。GD HEAD 为 `06edabc7fa64f943c704de38f81d56cf47d9b40b`；AF Develop HEAD 为 `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`，保留其既有补丁。candidate02 Manifest 摘要为 `036afc76901f24267f8ee59f379994ada54dc4b6aa01c72eb5865a355fcb0b4c`。

- 验收接线和 Owner：绝对路径 env02 Python 3.12.10 x64；`-I -B` 进入接线，实际导入 env02 安装 AF；原 Manager 以 `-I -S -B` 调用安装副本 service_owner.py。无 Standard 扩展时原 `owner_interpreter()` 返回 env02，没有其他环境回退。
- GUI：使用同一个 env02 显式执行原 `D:\Projects\abqjobpilot_dev\launch_gui.py`。它把 Development 根放到模块搜索路径首位，因此 **GUI 加载 checkout AF，而非安装副本**。两者 123 文件逐项匹配 candidate02；GUI 引导文件另行固定摘要。不能把默认 VBS 的环境选择当作 env02 证据。
- GUI 显示偏好使用原有 `ABQJOBPILOT_UI_PREFS` 进程级入口，指向本轮新文件，不读取原 Recent 列表；不改全局环境变量。Tk/真实 GUI 显示尚未实测。
- 本轮实际运行过限定离线程序和纯文件/导入预检；没有运行 `launch_gui.py`、宿主探针或真实 execute 分支。

## 唯一控制者及证据顺序

为避免两个写入者，**本次由验收接线调用原 Lifecycle start/stop；GUI 只连接、查看，禁止点击 Start/Stop**。因此未来证明的是原公共 API 模式，不宣称 GUI 按钮是本次 Owner 的创建者。这不是第二启动路径：接线无 Popen/CreateProcess/service_owner 调用，所有创建仍在原 `ServiceLifecycleManager.start()` 中。

1. 重算候选/解释器/GUI 摘要并核对实际 AF import 路径，人工确认；独占创建新任务根。已有根、部分文件或重复 claim 均拒绝，不复用。
2. 原 `create_project` 创建全新 TEST_ONLY Project；无 Standard/process fixture、PAUSED、空 slot、零 jobs/Plan/Grant/Run/执行 Receipt。生命周期 DPAPI capability 不是执行 Grant。
3. 操作者在原 GUI 打开新 Project，保持 GUI、普通控制台和 Windows 会话存活；在接线输入 `GUI READY`。该等待在 Owner 创建之前。
4. 先持久化 START_INTENT，再调用原 start 一次；只接受 `CONNECTED` 且 `created=true`。STARTING、响应丢失或已存在 Owner 都停止，不补发。
5. 原 connect/discover 认证 Project/context/Owner/start_id；核对 ready/host 记录、env02 executable、基准 Python 映像、Owner 磁盘 stdout/stderr 和 TEST_ONLY backend。
6. 用原 `ProcessReference(pid, identity, cleanup=False)` 获取并保持同一只读同步 HANDLE，复查 health/仍存活；成功查询并记录 Owner Job=true/false。未知查询仍拒绝，完整祖先链保持 UNKNOWN。持久保存绑定身份，短时观察 3 秒。
7. 再核对身份/零计数，持久化 STOP_INTENT；以 `e4g_stop_<本次 start_id>` 调原 idle stop 一次。精确核对其回执，不接受重放当成本次新成功。
8. 在同一 HANDLE 上最多等待 10 秒，要求 signaled、退出码 0、身份一致。原 `_stopped()` 核对 stopped.json、owner.json 及 SQLite 持久管理回执；再比对本次返回值和最终零计数，检查 CloseHandle 成功。
9. **最终唯一成功依据是持久 RESULT=`E4G_SESSION_PASS` 且 cleanup 为空。** 先写的 VERIFIED 只代表收尾证据检查完成，不能单独当 PASS；RESULT 写入失败也为 UNKNOWN。

任一不确定性都不自动补偿 stop、不重新 start、不换键、不重开 PID、不 kill、不清理。只保存失败阶段，退出验收操作，保留目录及原会话供评审；若 Owner 可能仍活着，不把 CLI 返回当作 Owner 已退出。已知本轮只读句柄的关闭不修改/终止进程。

## 限定离线测试

`tests/integration/d7_e4g_offline_checks.py`：**21 tests / 0 failures / 0 errors**；Ruff 通过。原 E1 `_connect_audit` 与 `_deny_production` 代码按冻结 SHA 复用；在接线导入前替换原 issuer 函数对象，覆盖已捕获别名；另拒绝所有 SQLite/native/network，并封闭真实 start/stop/create_project 函数。未进行 pytest 广泛收集，未改 E1 旧白名单。

覆盖：Job true/false 与查询失败、身份变化、启动 UNKNOWN/丢响应/已存在 Owner、IPC 失败、绑定时退出、停止回执字段冲突、重放、同 HANDLE 退出码/身份/超时、持久回执缺失、持久化故障、重复操作、关闭失败、脱敏输出及原 API 转发。实际创建数据库连接 0、生产 Grant 增量 0、Run 增量 0、Owner 0。仅创建并保留新的 `GDCAE-E4G-OFFLINE-*` 目录内 Journal 测试文件；未访问历史事故数据库。

**E1 守卫仅在本轮离线测试进程装载，不会自动进入未来真实 GUI/Owner。** 未来试验的产品边界是新 TEST_ONLY Project、无真实 backend、零 Plan/Grant/Run和限定操作，而非声称具备 E1 跨进程隔离或抗同用户恶意代码能力。空 Owner 试验不调用 ManagedScope，不能验收 Solver、Route C Standard、真实 DAT 或 GUI 显示同步。

## 待批准的唯一实机操作卡（当前禁止执行）

单独审批范围：一份新 Project、一个普通用户 GUI、一个验收进程、一次原 Owner start 和一次 idle stop；禁止其他 Start/Stop、授权/提交/派发、Run、Solver、Datacheck、ODB。新任务根及 UI 偏好文件当前均不存在，精确位置见 Manifest。

批准后由操作者在 **Codex 之外的普通、非提升控制台** 执行以下操作。先核对 Manifest 及下列 source_files 摘要，再在启动 GUI 前核对全部候选来源；发现任何变化、已有任务目录或已有偏好文件即停止，不调整或重试。这里的脚本和 Manifest 是可信本机用户文件，不声称抵御同权限并行恶意替换。Manifest SHA-256：`2deef51980930a5c8b1ad811230732fecd503958e38bae4b832acd367c094e72`。

```powershell
# 仅供后续明确批准后执行；本轮未运行。
$base = 'C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local'
$py = "$base\GDCAE-D7-R2F-E2-20261101-A01\env02\Scripts\python.exe"
$task = "$base\GDCAE-D7-E4G-20261102-A01"
$prefs = "$base\GDCAE-D7-E4G-20261102-A01.ui.json"
$bytes = [IO.File]::ReadAllBytes('D:\Projects\Goal-Driven-CAE-Orchestrator\docs\milestones\D7-E4G_ACCEPTANCE_MANIFEST.json')
$hasher = [Security.Cryptography.SHA256]::Create()
try { $digest = [BitConverter]::ToString($hasher.ComputeHash($bytes)).Replace('-','').ToLowerInvariant() } finally { $hasher.Dispose() }
if ($digest -ne '2deef51980930a5c8b1ad811230732fecd503958e38bae4b832acd367c094e72') { throw 'E4G_MANIFEST_DRIFT_STOP' }
$manifest = [Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
if ((Test-Path -LiteralPath $task) -or (Test-Path -LiteralPath $prefs)) { throw 'E4G_EXISTING_TARGET_STOP' }
foreach ($entry in $manifest.source_files.PSObject.Properties) {
  if ((Get-FileHash -LiteralPath $entry.Name -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant() -ne $entry.Value) { throw 'E4G_SOURCE_DRIFT_STOP' }
}
if ((Get-FileHash -LiteralPath $py -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant() -ne $manifest.interpreter_sha256) { throw 'E4G_INTERPRETER_DRIFT_STOP' }
if ((Get-FileHash -LiteralPath $manifest.base_interpreter -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant() -ne $manifest.base_interpreter_sha256) { throw 'E4G_BASE_INTERPRETER_DRIFT_STOP' }
& $py -I -B -c "import runpy; runpy.run_path(r'D:\Projects\Goal-Driven-CAE-Orchestrator\tests\integration\d7_e4g_lifecycle.py')['verify_runtime']()"
if ($LASTEXITCODE -ne 0) { throw 'E4G_RUNTIME_PREFLIGHT_STOP' }
$env:ABQJOBPILOT_UI_PREFS = $prefs  # 仅当前控制台及其 GUI 子进程；不修改用户/机器环境
Start-Process -FilePath $py -ArgumentList @('-I','-B','D:\Projects\abqjobpilot_dev\launch_gui.py') -WorkingDirectory 'D:\Projects\abqjobpilot_dev' -WindowStyle Hidden
& $py -I -B 'D:\Projects\Goal-Driven-CAE-Orchestrator\tests\integration\d7_e4g_lifecycle.py' --execute-approved-single-attempt
```

`Start-Process` 只启动原 GUI，隐藏其辅助控制台；原 Tk 窗口供操作者观察，未配置 breakaway/提权。GUI 未出现或有错误时，**不输入任何确认，停止**。确认 `E4G SINGLE TEST_ONLY` 后创建新 Project；在 GUI 用 Open 选择 `$task\af-test-only`，不使用 Recent，不进入 Classic，不点 Start/Stop。随后仅输入 `GUI READY`，程序完成唯一 API 启停并返回脱敏 JSON。GUI 是否真正显示连接状态由操作者另行报告，不由程序的 3 秒等待推定。

原始身份、host 元数据和管理回执仅保存到新任务根；不向聊天复制 PID/Owner ID/DPAPI 材料。回传程序脱敏 JSON；任何 UNKNOWN 保持原会话，不自行再点停止或重启。仅待审批准，不执行本卡。

## 独立复核与交付边界

独立 Reviewer 已预审精确 21 方法并允许离线执行；最终只读复核结论为 **E4G_FINAL_REVIEW_PASS_LIMITED / REAL_NOT_RUN**。指出的三项边界已纳入本文：VERIFIED 非最终 PASS、E1 不跨进程继承、GUI 非本次创建者且显示未证明。操作卡经复核已将解释器、基础解释器及完整候选来源检查前置到 GUI 启动之前。Reviewer 没有重复运行测试或进行实机操作；其结论不授予执行权限。

最终源码摘要见 Manifest；实机仍未运行。GD 仅新增上述四个文件，AF、共享环境、正式 Plugin、F2 历史均未改，无提交或推送。Git tracked diff 检查与四个新文件的 no-index 空白检查未发现错误；Git 提示未来可能执行 LF→CRLF 转换，任何未来字节变化都须重新冻结摘要，不能沿用本次 Manifest。
