# D7-E4 / E4-F — 单次 TEST_ONLY Owner 生命周期审批单

2026-11-01 · **BLOCKED_E4_INDEPENDENT_HOST_NOT_OBSERVED**

E4-F 离线检查通过，独立宿主尚未实测；不建议现在批准 Owner。保留原 E4 `BLOCKED_E4_HOST_AND_ORIGINAL_HANDLE_CLOSEOUT_UNQUALIFIED`：当时 Codex 工具进程 in_job=true、直接 flags=0x3000、外层链 UNKNOWN。本次修正“必须取得原 Popen 创建句柄”的技术判断，不追认历史退出。E3 PASS 沿用用户裁定；事故资料及旧 Owner/Job UNKNOWN 均不变。

## 1. 冻结对象

`R = C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-R2F-E2-20261101-A01`

| 对象 | 实际核验 |
|---|---|
| GD / AF HEAD | `a75a614f9738af8f257fd490ceec2df4c012ea19` / `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`，保留原未提交层 |
| Manifest | `R\candidate02\D7-R2F-E2_CANDIDATE_MANIFEST.json`；SHA-256 `036afc76901f24267f8ee59f379994ada54dc4b6aa01c72eb5865a355fcb0b4c` |
| 解释器 | `R\env02\Scripts\python.exe`，实测 CPython 3.12.10 x64；SHA-256 `0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14` |
| 安装及来源 | GD/AF distribution 均 `0.0.0+d7r2f`；AF 123 文件在 env02、Develop 与 Manifest 全部匹配；未重建/重装 |

实际 Owner 入口为 `R\env02\Lib\site-packages\abqjobpilot\service_owner.py`，SHA-256 `554a7b6efcb1a2882736f281b4b778f3a13336dd29a2ef3d351dabeb697953eb`；Lifecycle `8834b2df2291c8d9861aa5ef23ce25cb376d40a993c1e051c81d7dbed1c57270`；ProcessReference `1c3f7961c49c72d55c011d095404413668ea606488db49e05d5c182ad99e453d`。探针强制复核以上文件。无 standard_extension 的纯 TEST_ONLY 路径选 env02；不代表 Route C 固定解释器或 Standard 已验证。

## 2. 宿主与退出证据

**独立宿主：**开始菜单第一层、非提升 Windows PowerShell 5.1。探针只查询该窗口和实际 env02 控制器的只读 HANDLE、Job 归属及 token elevation；`IsProcessInJob(handle,NULL)` 必须 API 成功且两者 false。true/查询失败即阻断，不提权、不 breakaway、不修改 Job。开始菜单来源仍需操作者确认，不能从指定 PID 反推；非提升 token 不等于账户不属于管理员组。观察仅代表该时点，获批实际控制器 start 前须重查，存活 Owner 须另查；Owner 当前为 NOT_YET_OBSERVED。[微软 API](https://learn.microsoft.com/en-us/windows/win32/api/jobapi/nf-jobapi-isprocessinjob)

**无需 AF 生产补丁：**`service_discovery.discover()` 绑定精确 Project/context、DPAPI 端点与认证 health；其临时句柄会关闭。现有 `ProcessReference(pid, expected, cleanup=False)` 可按 PID、创建时间、映像重新绑定仍存活的同一进程对象，保持 SYNCHRONIZE + QUERY_LIMITED_INFORMATION，不含 terminate 权限。无需原 Popen 创建句柄。[微软访问权](https://learn.microsoft.com/en-us/windows/win32/procthread/process-security-and-access-rights)

唯一顺序：原 Lifecycle.start 一次 → connect 认证 → endpoint 核对 Project/context/Owner、health 核对 start_id/process → 获取上述句柄 → 未退出/无 Job → 再次 health/存活核对 → 持久记录绑定身份 → 保持同一 HANDLE 跨越原 Lifecycle.stop → 最多 10 秒等待 signaled 且 GetExitCodeProcess=0 → 核对同 key 持久管理回执及 stopped.json → 检查 CloseHandle 返回值。stop 回执、PID 消失、失联、stopped.json 单独都不是退出证明。只证明精确 Owner，不证明未知后代全家族；venv transport PID 不得冒充 Owner。

## 3. 唯一待批准实验及停止条件

新目标（再次确认不存在，未创建）：`C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-E4-20261101-A01\af-test-only`。

仅原 `product_project.create_project`：product-test-lifecycle-v1、process_config=null、无 Standard 扩展、fake-v1 唯一 backend、PAUSED、空 slot、Plan/Grant/Run=0。仅原 `ServiceLifecycleManager.start(wait_seconds=8)` → 认证 health/只读 IPC → 原 idle stop 一次；不直接调用 service_owner、不 resume/submit、不派发 Fake Run。生命周期 capability 不是执行 Grant。上述零计数是未来检查条件，非已创建 Project 的结果。

未来启动前还须审查该单次操作对身份持久记录、回执核对及 E1 issuer/别名/直接 Grant 写入拒绝的实际绑定；本次观察 helper 不包含完整生命周期操作，不可直接用于 start。预计副作用仅新目录内项目/SQLite、DPAPI 生命周期及连接材料、锁、启动账本、日志及管理回执，全部保留。最终零 Plan/Grant/Run、PAUSED。

任何身份、Job、IPC、退出、回执或关闭 UNKNOWN：停止实验动作，仅同身份/同 key 只读对账；不重试 start/stop、不换项目、不按 PID 重新打开替代句柄、不扫描/终止进程或清理。已知本轮观察句柄的正常关闭不涉及未知 Job。真实 Owner/完整收尾均尚未验证。

## 4. 离线验证、审查和一次人工步骤

仅新增 `tests/integration/d7_e4f_observation.py`（只读探针/观察 helper，无 start/stop/Project/issuer）及 `d7_e4f_offline_checks.py`。独立 Reviewer 预审精确 16 方法后，env02 `-I -B` 实测 **16 tests / 0 failures / 0 errors**；安装版 ProcessReference 路径/摘要匹配，Windows 调用全部模拟。覆盖 PID 复用、身份/映像失配、握手竞态、Job true/未知、句柄/等待/退出码失败、超时、IPC UNKNOWN、关闭失败；Ruff、git diff --check 通过。

预导入守卫只允许 AF models/process_handles，拒绝 issuer/Project/Lifecycle/store 导入，禁止 SQLite/native/network。不收集旧 pytest；唯一 SQLite 请求是被拒绝的内存连接负测：实际连接 0、Grant 增量 0、Owner 0。此为独立审查的新离线清单，不宣称扩展 E1 旧白名单。token WinAPI 为静态审查，host 分支为模拟；Reviewer 确认无须新启动路径，但不构成现场宿主/退出 PASS。

**唯一人工步骤：**从开始菜单打开普通 Windows PowerShell 5.1，在第一层窗口原样粘贴此只读命令，返回脱敏 JSON 并确认窗口来源；不要另开嵌套 Shell。

```powershell
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) { throw 'BLOCKED_PS51_REQUIRED' }; & 'C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-R2F-E2-20261101-A01\env02\Scripts\python.exe' -I -B 'D:\Projects\Goal-Driven-CAE-Orchestrator\tests\integration\d7_e4f_observation.py' --console-pid $PID
```

探针 SHA-256：`5d88b575db54990b804f728983c1574cfaccaa4fa67b1df062e3ea6c2506d3c8`；测试文件 `e993fa78f3b202eb5691ba2f896f5fa4b099391a4be52fba47545f9c165c2ca4`。探针不写文件、不创建子进程、不输出 PID/原始异常/凭据；失败立即停止，不自动重试。脚本在本机用户可写目录，采用既定可信本机模式，不宣称抗同权限恶意替换。

最终独立复核：`E4F_FINAL_REVIEW_PASS_LIMITED`，Reviewer 独立计算两份新增文件摘要并确认匹配；未发现阻止交付只读操作卡的问题，不批准真实生命周期实验。

本轮未启动 Owner/求解器、未签发 Grant、未访问事故 DB 或 Stable、未改 AF/共享环境/Plugin，无 Git 提交或推送。保持 BLOCKED，等待只读宿主回执；后续 Owner 仍须另行单次授权。
