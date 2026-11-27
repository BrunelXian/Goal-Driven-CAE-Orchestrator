# D7-E4G-A02 — 冻结候选与分步操作卡

2026-11-02 · **OFFLINE_TESTED / A02_REAL_NOT_RUN / SEPARATE_APPROVAL_REQUIRED**

本卡当前只供审阅，不构成实机执行授权。只增加 A02 薄入口及离线测试，不改 AF API，也不改 A01 接线、Manifest、操作卡或 F2 失败记录。

## 已核实的 A01 现场

- A01 任务根不存在；独立 `GDCAE-D7-E4G-20261102-A01.ui.json` 存在，132 字节，属性 Archive，无 reparse 属性。创建/最后修改时间均为 `2026-11-02T08:02:27.9344306Z`，SHA-256 `ce0e646b9d0b2c1be3f5043d90fb56aaadc8c1501a75c4e2901c38cf4e76f1ca`。仅读取文件元数据并计算摘要，未解析或输出内容。
- `abqjobpilot/ui_resources.py:36` 从 `ABQJOBPILOT_UI_PREFS` 选择偏好位置；`:49–58` 保存显示字段并通过临时文件 replace。`desktop_workspace.py:328,493` 有语言/窗口布局保存调用。因此 GUI 显示后单独留下偏好文件符合源码机制，不表示创建了 AF Project。具体写入者并无独立证据。
- 首次 `PREFLIGHT_OR_RESERVATION` 的输入根因仍 UNKNOWN；第二次 `E4G_EXISTING_TARGET_STOP` 与偏好文件存在相符，拒绝规则有效。用户报告独立输入测试 `INPUT_OK`，不能追溯证明首次输入流状态。均保持 BLOCKED，不删除文件、不重跑 A01。

## 最小差异与来源

原接线 TASK/PROJECT 硬编码 A01，没有路径参数；GUI 本身已有进程级偏好路径入口。新 `tests/integration/d7_e4g_a02.py` 先核验 A01 源码 SHA，再从同一内存字节加载原逻辑，仅绑定固定 A02 TASK/PROJECT，并检查精确 GUI 偏好环境变量。无任意目录或自动换身份接口，没有第二启动器。

原接线 SHA：`6f28256b6126349e46785aa1e67de0019c67de750b1df82f1a634cd5c8164c2a`。

A02 入口 SHA：`d162a9e60b4c8e2a1bb3420c46a06c77fcb5ab2a5fa0ffc1ae011a17ac7970c4`。

A02 测试 SHA：`46f149a8ca6d6fdfa7c22a5b7181a2711fcf839ab847af819bb8fa33bb6530ee`。

**冻结 Manifest：** `D:\Projects\Goal-Driven-CAE-Orchestrator\docs\milestones\D7-E4G_A02_MANIFEST.json`

**SHA-256：** `e0617dfc17ff5990512845bb546d2e5465d33ee0e3ed55d4805e8f9b2b94b366`。

仍使用 candidate02 的 env02 Python 3.12.10 x64、Core `aegiscae 0.0.0+d7r2f`、AF distribution `abqjobpilot-gdcae-internal 0.0.0+d7r2f`。本轮先误用模块名 `abqjobpilot` 查询 distribution，得到 PackageNotFoundError；随后按实际 dist-info 名核实成功，不是安装漂移，未更改环境。

GUI 仍通过原 launch_gui.py 加载已逐文件核验的 AF checkout；接线/Owner 加载安装 AF。无 Standard 扩展时原 Owner 解释器绑定 env02，不回退 LangChainEnv。完整 123 文件匹配由原 verify_runtime 复核。

## 实际离线验收

独立 Reviewer 预审精确集合通过后，由主 Agent 执行 env02 `-I -B tests/integration/d7_e4g_a02_offline_checks.py`。继承原 21 项并新增 5 项：固定 A02 身份、目标/偏好存在拒绝、预检失败脱敏、偏好绑定拒绝与转发、EOF/空输入/中断及正确确认的隔离测试。原 E1 守卫先于新入口加载；生产 issuer、直接 SQLite、真实 start/stop/create_project、原生和网络操作均拒绝。

实际回执：26 tests、0 failures、0 errors；Owner/Grant/Run/数据库连接新增均 0，native=MOCKED。仅新增保留 `GDCAE-E4G-A02-OFFLINE-3g9ajiw1` 下 Journal 样例。Ruff 通过。A02 实机任务根及偏好文件尚未创建。

最终独立只读复核通过：摘要、三步操作顺序、A01 保留与有限资格边界一致，可交付待单次实机批准；Reviewer 未执行测试、GUI、探针或 Owner。三段 PowerShell 仅做静态解析，均零解析错误。diff 空白检查无错误；Git 提示未来可能进行 LF→CRLF 转换，冻结字节若变化须重新审查摘要，不得沿用本次身份。

输入逻辑未修改，仍精确匹配 `E4G SINGLE TEST_ONLY`，失败不重读、不自动重试。本轮不把 mock 输入测试当成实机输入问题已修复。

## 下一次单独审批范围

只批准时才可执行下列三步：一个新 A02 TEST_ONLY Project、一个普通用户原 GUI、一次原 ServiceLifecycleManager start → authenticated IPC → 同一 ProcessReference HANDLE → idle stop。GUI 仅观察，禁止 GUI Start/Stop；零 Plan/Grant/Run/Solver，PAUSED，无 Standard/process fixture。E1 守卫仅限离线测试，不宣称会跨进程进入实机 Owner。

新路径（不得替换或复用 A01）：

- 任务根：`C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-E4G-20261102-A02`
- Project：上述目录的 `af-test-only`
- UI：任务根同级的 `GDCAE-D7-E4G-20261102-A02.ui.json`

三段必须分开操作，在 Codex 之外同一个普通、非提升 Windows PowerShell 控制台进行。不要整卡批量粘贴，不要使用管道传入 Python，不要启动嵌套 Shell。既有 A01 GUI/文件不作为本次证据，不自动关闭、接管或清理。

### 第一步：只读预检（未来批准后）

只粘贴本段，等待返回 `E4G_A02_PREFLIGHT_PASS` 及 PowerShell 提示符。任何异常或 BLOCKED 立即停止，不继续第二步。

```powershell
$ErrorActionPreference = 'Stop'
$a02Ready = $false
$base = 'C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local'
$py = "$base\GDCAE-D7-R2F-E2-20261101-A01\env02\Scripts\python.exe"
$entry = 'D:\Projects\Goal-Driven-CAE-Orchestrator\tests\integration\d7_e4g_a02.py'
$bytes = [IO.File]::ReadAllBytes('D:\Projects\Goal-Driven-CAE-Orchestrator\docs\milestones\D7-E4G_A02_MANIFEST.json')
$hasher = [Security.Cryptography.SHA256]::Create()
try { $digest = [BitConverter]::ToString($hasher.ComputeHash($bytes)).Replace('-','').ToLowerInvariant() } finally { $hasher.Dispose() }
if ($digest -ne 'e0617dfc17ff5990512845bb546d2e5465d33ee0e3ed55d4805e8f9b2b94b366') { throw 'A02_MANIFEST_DRIFT_STOP' }
$manifest = [Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
foreach ($item in $manifest.source_files.PSObject.Properties) {
  if ((Get-FileHash -LiteralPath $item.Name -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Value) { throw 'A02_SOURCE_DRIFT_STOP' }
}
if ((Get-FileHash -LiteralPath $py -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.interpreter_sha256) { throw 'A02_INTERPRETER_DRIFT_STOP' }
if ((Get-FileHash -LiteralPath $manifest.base_interpreter -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.base_interpreter_sha256) { throw 'A02_BASE_INTERPRETER_DRIFT_STOP' }
if ((Test-Path -LiteralPath $manifest.task_root) -or (Test-Path -LiteralPath $manifest.gui_preferences)) { throw 'E4G_EXISTING_TARGET_STOP' }
& $py -I -B $entry --preflight-only
if ($LASTEXITCODE -ne 0) { throw 'A02_PREFLIGHT_STOP' }
$a02Ready = $true
```

### 第二步：单独启动原 GUI（未来批准后）

仅在第一步全部成功后粘贴。环境变量只改当前控制台及其子进程，不改用户/机器设置。GUI 可以正常保存 A02 偏好；这不许可重复执行第一步或换一个任务身份。

```powershell
if (-not $a02Ready) { throw 'A02_NOT_QUALIFIED_STOP' }
if ((Test-Path -LiteralPath $manifest.task_root) -or (Test-Path -LiteralPath $manifest.gui_preferences)) { throw 'E4G_EXISTING_TARGET_STOP' }
$a02Ready = $false
$env:ABQJOBPILOT_UI_PREFS = $manifest.gui_preferences
Start-Process -FilePath $py -ArgumentList @('-I','-B','D:\Projects\abqjobpilot_dev\launch_gui.py') -WorkingDirectory 'D:\Projects\abqjobpilot_dev' -WindowStyle Hidden
```

等待新 GUI 实际显示及控制台返回提示符。GUI 出错或身份不清即停止；不要点击旧 GUI 或任何 Start/Stop。隐藏的是辅助控制台，原 Tk 窗口仍可见；没有 breakaway 或提权。

### 第三步：单独交互命令（未来批准后，仅一次）

**仅复制下面一行命令，不含后面的批准短语，不附带其他命令。** 回车后等待 Python 自己的提示，再手工输入短语。

```powershell
& $py -I -B $entry --execute-approved-single-attempt
```

1. 出现 `Separate approval required. Type E4G SINGLE TEST_ONLY:` 后才手工输入 `E4G SINGLE TEST_ONLY` 并回车；若它提前退出，停止，不重发命令。
2. 出现 `PROJECT_PREPARED` 后，在刚启动的新 GUI 用 Open 选择精确 A02 `af-test-only`，不使用 Recent/Classic、不点击 Start/Stop。
3. 返回控制台，仅在第二个提示下输入 `GUI READY`。接线独占完成原 API 的一次 start/stop，原有 8 秒启动、3 秒观察及 10 秒退出等待不变。
4. 仅回传脱敏 JSON；真实身份和回执保留在 A02。任何 UNKNOWN 不自动 stop、重启、杀进程、重开 PID 或清理。保留会话和现场等待评审。

有限资格只证明本次受监督会话内退出；Job true 可记录但完整祖先约束仍 UNKNOWN，不保证跨会话/Job 退出存活。最终 PASS 必须是持久 RESULT 与关闭成功，不能用 VERIFIED、GUI 可见或停止响应替代。不涉及 ManagedScope、Standard、Solver、DAT 或真实 A 资格。
