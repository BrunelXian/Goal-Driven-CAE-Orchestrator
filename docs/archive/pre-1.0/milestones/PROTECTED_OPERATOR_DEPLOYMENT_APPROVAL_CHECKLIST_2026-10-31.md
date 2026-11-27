# Protected Operator 精确部署审批清单

日期：2026-10-31。状态：**FOUNDATION_PREPARATION_LIMITED_PASS；OPERATOR_ACTIVATION_BLOCKED**。
本清单尚未获系统级实施批准。仅请求下表明确的基础部署；不请求启用账户、创建真实 Project/能力、Owner、Grant、Solver 或真实 A。

## 一、实际主体与主机

本轮直接查询了 Codex 工具所启动的当前进程令牌，没有扫描其他进程、会话或旧 Owner。

| 项目 | 实际观察 |
|---|---|
| Windows | 10.0.26300；主机 MachineGuid 的摘要已绑定最终私有计划 |
| 当前执行令牌 | 未提升；admin/linked-admin=true；没有线程模拟身份；in_job=true |
| 已启用权限 | SeChangeNotifyPrivilege；未提升任何权限 |
| 当前实际 SID | 原值仅保存于私有 identity/plan；公开关联摘要 `1c586d44927c0c43d61844ae4cd63f1d7f3dba8850cfeb8e2d86911a903e6757` |
| 拟议本地账户 | `GDCAEResearch`、`GDCAEIssuer` 精确本机查找均为 ABSENT（不存在），不是忽略查找失败后猜测不存在 |
| 目标目录/能力 | code、rules、config、projects parent、未来 A capability 全部 NOT_PROVISIONED |

这是实际文件/命令工具进程的主体证据，不是对未查询的 Desktop UI 进程身份的推断。
当前 Codex 工具主体既不是拟议 Research，也不是拟议 Issuer；其管理员关联不能作为隔离证明。
**仅创建或测试一个未被 Codex 使用的低权限账户不算完成切换。** 后续须在新 Research Windows 登录会话中通过官方方式使用 Codex，实际执行本只读 probe，并由独立审查核对工具调用及 SID 与管理员部署回执一致。不能复制旧 Codex 登录秘密、会话或环境来伪装切换。

## 二、请求批准的精确变化

### 账户

- 新建本机 `GDCAEResearch` 与 `GDCAEIssuer`，使用各自新密码，仅加入内置 Users 组。
- 两账户**保持 Disabled**。不添加 Administrators、服务登录权、自动登录、计划任务或 Windows 服务；不改变既有账户/组/安全策略。
- 密码只在独立管理员控制台以 SecureString 提示输入，不进入命令参数、计划、回执、日志或 Agent。
- 新 SID 只能在实际创建时确定，由管理员私有回执记录；不能预造 SID。遇到同名账户/目录即停止，不接管、不重用、不覆盖。
- Research 后续承载真正的 Codex 科研工具进程。Issuer 仅供人类受保护控制台和原 AF Owner 使用，不运行 Codex/普通 Agent。

### 新目录与 ACL

所有新目录创建时采用显式受保护 DACL，关闭父目录 ACE 继承；所有者为 Administrators，SYSTEM/Administrators FullControl。
不会调整 `C:/`、Program Files、ProgramData 或其他既有祖先 ACL。

| 新路径 | Research | Issuer | 用途 |
|---|---|---|---|
| `C:/ProgramData/GDCAE Operator Preparation` | 无 | 无 | 人工管理员先建立的受保护暂存区；5 个脚本、私有计划、首个持久 intent；仅 Admin/SYSTEM |
| `C:/Program Files/GDCAE Operator` | ReadAndExecute | ReadAndExecute | 按冻结清单复制代码/运行时/只读 probe；任何新主体均不可改冻结规则 |
| `C:/ProgramData/GDCAE Operator` | 无 | ReadAndExecute | 固定状态父目录；Issuer 不得在这里任意新增顶层项 |
| `.../config` | 无 | ReadAndExecute | 后续管理员签定配置；本轮部署脚本不生成有执行效力的配置 |
| `.../projects` | 无 | Modify | 后续另批后，Issuer 在最终 `projects/A` 原地创建全新 AF Product；脚本本身不创建 A |
| `.../audit`、`.../review` | 无 | Modify | 将来的受控审阅/证据；Issuer 可修改，**不声称 append-only 或不可篡改** |
| `.../deployment` | 无 | 无 | 管理员私有部署回执；包含实际新 SID、intent 和文件摘要 |

未来 `projects/A/private/standard-operator.json`、AF SQLite、engineering/scratch 均属于同一最终 AF test_root 的私有子树；不把工程目录放到 context 之外。实际数据库/输出精确位置仍需由新 ProjectContext/Plan 冻结。
本次只复制源码/二进制作为不激活的候选，不安装包、不修改 LangChainEnv、系统 Python、PATH 或全局 Codex 配置。

### 已冻结候选与运行方式

唯一审批候选：

`C:/Users/wuxia/AppData/Local/GDCAE-G3-D3-OFFLINE-20261030-A01/D6-20261031-A01/OperatorPreparation-20261031-A01/OPERATOR_FOUNDATION_REVIEW_PACKAGE.zip`

- ZIP：12,690,835 bytes，SHA-256 `c7c05574479f51a3af9c9a9821e6b17108d1ec6fe5dc0774ac1ae08fd6a67789`。
- 最终计划：同目录 `DEPLOYMENT_PLAN_SNAPSHOT.private.json`，SHA-256 `b8bbfe81cf5c2b070ab2dfa3f7432587f4501dd51c52e37821996bd778dae9c7`。
- 887 个明确 payload 文件，总计 35,456,592 bytes。包括 GD/AF `.py` 白名单、CPython 3.12 解释器/标准库/DLL/PYD、七个精确 pywin32 依赖及只读 probe/audit 两文件。没有历史报告、账户秘密、模型工程、运行数据库或测试结果。
- 库存是静态文件闭包候选；动态导入、资源闭包、ABI、`-I -S -B` 下的 pywin32 加载**未通过**。不将未执行的库存称为可用运行环境。
- ZIP 中包含 887 payload、5 个脚本和 1 个私有计划，共 893 条；包含本机身份映射，不是公开发布包。
- 计划使用本机任务 snapshot 的绝对源路径。Apply 逐个锁定读取、验证字节摘要后复制；不会自行从 ZIP 重写来源路径。换机器、换源路径、文件变化须重新冻结并批准。

脚本位于本仓库 `operator_deployment/`：

| 文件 | 行为 |
|---|---|
| `Deploy-Operator.ps1` | 默认 DryRun；Apply 需要精确计划 SHA、固定确认词、独立提升管理员控制台、无 Job、无 impersonation、受保护暂存区及全部守卫通过 |
| `Undo-Operator.ps1` | 默认 DryRun；仅对精确回执中的 disabled 新 SID 再禁用；保留全部文件和 ACL；已启用/已使用/UNKNOWN 时停止人工审查 |
| `Operator.Common.ps1` | 窄范围路径/摘要/权限检查、原子创建受保护目录、CreateNew 复制、Flush 持久 intent/receipt；不创建进程或自动提权 |
| `identity_probe.py`、`audit.py` | 当前 token、固定路径 AccessCheck，只读元数据；不读取能力字节、不写测试 Grant/数据库 |

PowerShell 要求 Windows x64 7.4+；本机实际解析/dry-run使用7.6.5。所有入口均没有 RunAs 自动提升、服务安装或执行 Solver 的动作。
未来调用形状（**本轮没有执行 Apply**）：

```powershell
# 仅系统级批准后，在独立管理员控制台、受保护暂存区内执行。
.\Deploy-Operator.ps1 -PlanPath .\DEPLOYMENT_PLAN.private.json
.\Deploy-Operator.ps1 -PlanPath .\DEPLOYMENT_PLAN.private.json -Mode Apply `
  -ApprovedPlanSha256 b8bbfe81cf5c2b070ab2dfa3f7432587f4501dd51c52e37821996bd778dae9c7 `
  -HumanApproval APPROVE_FOUNDATION_ONLY
```

**外部信任前提：** 管理员须先在现有 Codex 宿主之外，从已核对上述 ZIP 摘要的字节建立 Admin/SYSTEM-only 暂存区，放入5脚本和最终计划，再运行。脚本自校验不能认证已被替换的入口；摘要也不是签名。入口在加载 Common 前检查暂存对象及全部祖先的 reparse、owner、有效替换权限和保密 ACL。确认字符串、管理员令牌和无 Job 条件都不能独立证明“人类”，人类操作仍是外部审批前提。

## 三、真实双身份否定验收

账户启用与登录须另行批准。以下必须使用管理员回执中的实际 SID，不能仅看用户名或测试账号自述。

| 必须取得的真实证据 | 不接受的替代 |
|---|---|
| 新 Research 登录中，真正的 Codex 工具进程 SID 匹配，无 admin/linked-admin/impersonation | 只在普通低权限 PowerShell 测试后声称 Codex 已切换 |
| Research 对代码/规则/依赖/config 无写权；对能力无读权；对实际 AF DB/input/output 无写权 | 模拟 AccessCheck、父目录未创建、缺失文件导致读取失败 |
| Issuer 非管理员，能读运行材料及私有能力、修改允许的 Project 数据，但不能改规则/code/config/runtime | Issuer 拥有 FullControl、可修改白名单或配置后自行通过 |
| 实际固定文件和祖先权限、实际 Grant 存储文件绑定、原接口拒绝无能力请求 | Agent 自报批准，或为了测试而签发一个真实 Grant |

`identity_probe.py --access` 已准备当前 token 的只读检查；缺失对象返回 NOT_PROVISIONED，不算拒绝访问证明。最终 AF DB 文件必须来自真实冻结 context；当前探测没有猜测 DB 路径。纯 `review_role_observations` 只检查诊断记录一致性，不认证记录发布者，不授予执行权。
Research 可在自己的目录伪造 JSON，但它不得被原受保护 Store/Grant 接口接纳；源码负测仍须与实际能力/存储访问拒绝一起审查。不能授予 Research issuer capability 来“跑通”连接。

## 四、必须保持的激活阻断

1. **受保护 runtime 与固定解释器冲突。** `standard_contract.py` 固定 LangChainEnv 路径；lifecycle 要求 Plan interpreter 与实际解释器相同；`rod_authority.protected_context` 要求解释器和所有 imports 在 CODE_ROOT。目前不能同时满足。下一轮只能对动态 rod 增加版本化受保护 runtime pin，保留旧 fixed 分支；不得 junction/伪装路径或放宽 custody。
2. **正常 INHERIT_ONLY ACE 的兼容缺陷。** 本轮实际 C:/、Program Files、ProgramData 有只对子项生效的继承条目。部署脚本按 Windows 语义跳过它们对当前祖先的权限判断，并在新根关闭继承；AF 当前 `WindowsCustody.check` 未处理该标志，仍可能错误阻断。AF 未改，禁止修改系统祖先 ACL 去迎合该判断。
3. **没有可执行的受保护 Operator CLI。** 已有正式 API 是 `RodProduct`、`prepare_rod_a_only`、`ServiceLifecycleManager.start`、`review_rod_a_console`、`StandardOperator.request`。选定入口是未来人类独立 Issuer Windows 登录控制台调用原 lifecycle API，**不是**直接执行 service_owner 或伪造 start-id。本轮不提供绕过原 lifecycle 的第二启动路径。
4. **身份/DPAPI不能搬家。** Product 的 host_binding 含创建者实际 SID 与 MachineGuid；DPAPI使用当前用户及 context/host entropy。当前 Project、lifecycle/operator/connection/standard capability、Plan/Grant 均不可复制接管。必须最终 Issuer 在最终路径原地新建。Research 账户直接 discover/打开 Issuer Product 也会被原 host_binding 拒绝，跨身份只读交付与来源认证仍未实现/资格化。
5. **独立主机生命周期未验证。** 当前工具进程 in_job=true，不用于启动。未来须人类登录 Issuer 的独立 Windows 桌面，在无当前宿主继承关系的控制台中重新查 token/Job；仅手动开控制台也不证明宿主退出后 Owner 存活。生命周期试验、Owner、Grant、真实 A 仍各自等精确授权。

以上发现不会清除历史 UNKNOWN/BLOCKED。基础账户/目录部署成功也不意味着可以启动真实 A。

## 五、风险与撤销

- 首次目标根创建之前，先在管理员暂存区持久写 `deployment-intent.json`。账户创建、分组、目录、复制有 intent/receipt；任何失败均不自动重试、接管、删除或回滚。
- 首个 root 创建后但主 receipt 未成功落地时，由外部 intent 记录 UNKNOWN；自动 Undo 拒绝缺少精确 receipt。需要人工核对，不靠猜 SID 或目录名补证据。
- 撤销只禁用已记录且仍 disabled 的两个精确新账户，保留目录、代码、配置、ACL、审计和旧资料。若账户已启用、SID变化、Project/config已有内容、intent未完成，则停止；不声称禁用账户会结束既有登录或进程。
- 该撤销是停止使用的保守撤销，不是恢复“从未创建过”的系统状态；完整删除或使用后撤权需新的精确审批。不扫描/终止未知进程，不改旧 ACL。
- 管理员可绕过保护；可信 Issuer 可修改其私有数据库/审计。bearer IPC 不证明对端 OS SID。共享环境/新用户许可证、登录凭据和 Codex激活均不自动迁移。

## 六、实际验收与本轮修改

- 实际 Python：`D:/XianLab/envs/LangChainEnv/Scripts/python.exe`，3.12.10；pytest9.1.0、pywin32 312。未安装或更改环境。
- 最终相关离线回归 `operator-prep-regression-final`：**205 passed，0 failed/error/skipped，2.30 s，native/network denied attempts=0**。覆盖新计划/路径/权限诊断负测、库存稳定性与旧 D4–D6 Operator 规则。
- 初次集成收集因测试模块导入路径失败；改用既有显式文件加载方式后通过。库存工具初期 Windows stat/fstat差异已在合成测试中修复；没有运行目标二进制。
- 默认部署 DryRun 对最终 snapshot 计划实际通过：2账户、887文件、NO_CHANGES、ACTIVATION_BLOCKED。三份 PowerShell AST 均0解析错误；内存 DACL 检查确认protected继承、Admin owner、合成新角色无写权。**没有调用 Apply，也没有实测 Windows账户创建或ACL写入API。**
- 撤销脚本的默认 DryRun 实际以 `UNDO_REQUIRES_EXACT_UNUSED_RECEIPT_NO_RETRY` 拒绝：本机尚未部署，不能凭空撤销。最终三处目标根仍不存在，Git暂存区为空。
- Ruff通过；Git diff检查通过（既有LF/CRLF提示保留）；未暂存、提交或推送。
- 独立 Reviewer 发现并推动修复：Undo启用状态检查、初始intent缺口、bootstrap先验证边界、probe异常隐私、路径校验一致性和audit.py包闭包。最终包893条逐条长度/摘要、当前snapshot及5脚本均零失配；未解压安装或运行。
- 最终独立结论：`LIMITED_FOUNDATION_PREPARATION_REVIEW_PASS` 和 `LIMITED_APPROVAL_DOCUMENT_REVIEW_PASS`，无必须修订项；Reviewer未重跑测试或执行OS修改，不授予部署/激活权限。
- GD新增：`operator_deployment/{preparation.py,identity_probe.py,frozen_inventory.py,Deploy-Operator.ps1,Undo-Operator.ps1,Operator.Common.ps1}`，两份 `test_operator_preparation.py`/`test_operator_frozen_inventory.py` 单测，以及本清单。原 `audit.py`只读复用，未修改。AF源码本轮零修改。
- 两仓HEAD保持 GD `69b144cea9aecc515e15cc830368972b09258af9`、AF `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`；历史未提交材料全部保留。

## 七、需要用户的最少操作

**现在只需裁定是否批准这份“基础部署、账户保持禁用”的精确清单；当前不要求登录、复制文件或提供 SID。**
批准后，一次独立管理员控制台操作完成已审候选的外部摘要核对、Admin-only暂存、DryRun及Apply，并交互输入两个新密码；不得从当前 Codex Job 中自动提权执行。
运行时/控制台/跨身份接缝关闭后，再单独批准启用账户：在真实 Research 登录中验收 Codex 工具主体，在独立 Issuer 登录中验收只读权限及宿主环境。真实 A 仍需另一份冻结 host/身份/Plan/模型/资源/输出与单次 Grant 的授权单。

微软接口依据：[New-LocalUser](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.localaccounts/new-localuser?view=powershell-5.1)、[IsProcessInJob](https://learn.microsoft.com/en-us/windows/win32/api/jobapi/nf-jobapi-isprocessinjob)、[ACE继承规则](https://learn.microsoft.com/en-us/windows/win32/secauthz/ace-inheritance-rules)。本轮仅使用相应只读查询及内存对象；账户/目录创建代码未经真实执行。
