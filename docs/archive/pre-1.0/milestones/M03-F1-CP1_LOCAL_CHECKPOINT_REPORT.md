# M03-F1-CP1 — F1 Offline Baseline Local Checkpoint

结果：**M03F1_OFFLINE_BASELINE_LOCAL_CHECKPOINT_PASS（限定离线基线）**。

任务书日期：2026-10-29。实际执行跨至 2026-10-30；回执时间（UTC+08:00）：2026-10-30T00:42:13+08:00。

本回执在唯一一次本地提交完成后生成，特意不纳入该提交，以记录真实 SHA；它属于获准交付文件，保持未跟踪。没有修改历史报告。

## Commit 与范围

- Branch：`main`
- Commit：`184245cc8a67859484406d70fb1e2d1cf2e347c7`
- Parent：`538bfae9a3a5fcea97970b9effc4f1f168490650`
- Subject：`checkpoint: M03-F1 Offline Baseline (real CLI ACK unverified)`
- 本轮提交数：1；13 个新增文件、4 个修改文件，共 17 个。
- 未 push、tag、release、触发 CI 或继续 R2A；提交命令只在本次进程中关闭自动 Git 清理，未修改全局配置。

## 本轮实际测试

| 检查 | Passed | Skipped | Failed / Error | Exit | 秒 |
|---|---:|---:|---|---:|---:|
| P1 输出边界重跑 | 34 | 0 | 0 / 0 | 0 | 1.16 |
| Runtime + architecture | 269 | 0 | 0 / 0 | 0 | 894.83 |
| 完整无 Solver 回归 | 845 | 21 | 0 / 0 | 0 | 2024.67 |
| ruff | — | — | — | 0 | 0.08 |
| diff | — | — | — | 0 | 0.08 |

额外 CP1 合成筛查：15 项拒绝检查、1 项干净样例通过。全部标记为新生成的非真实数据；敏感样例仅在内存使用，不写入 Git 或输出。测试计数来自本轮新隔离目录，不沿用 P1 历史结果，各次重叠用例不累加。

21 项跳过为未授权 live opt-in：M01-B 1 项、M01-C 1 项、M03-B 19 项。未当作真实集成通过。解释器为既有 LangChainEnv 的绝对路径，Python 3.12.10 / pytest 9.1.0 / SQLite 3.49.1；Ruff 0.12.0。没有安装或更新依赖。

命令通过已验收 P1 bounded runner：pytest 使用 -B、-q、禁用插件自动加载和缓存、独立 basetemp；focused 指定 Runtime 与架构测试，full 执行当前全库。Ruff 为 check --no-cache .；diff 为 git diff --check，暂存区另行执行 --cached --check。任意输出先被抑制，再返回固定计数/状态。

## 内容、状态与权限审查

初始状态精确为 4 tracked modifications / 17 untracked，index 空。17 个候选的 hash/size/role 快照已固定；候选、每个 staged blob 及最终 commit blob/diff 均经过限定隐私扫描，命中为 0。每个暂存文件与原审查快照及 Git 规范化 blob 身份比对通过；逐个明确文件 git add，无目录或通配符暂存。

历史证据仅在获准独立进程中投影固定标记和元数据，不回显原文。F1 PARTIAL、R1 BLOCKED_PRIVACY_OUTPUT、P1 限定 PASS 标记与用户已接受的裁定保持一致。标记存在不是完整语义审查，regex 零命中也不是通用信息流或全历史无秘密证明。文件摘要只是内容身份，不是不可篡改的安全证明。

Project-owned Runtime Sidecar / Option 1A、两笔公开 Workflow API 独立提交的 TEST_SYNTHETIC Decision、持久队列、单未决 intent、UNKNOWN 阻断、延迟暂停和合成隐私保护均保留。Runtime 阶段的 Project 逻辑 schema/history 只读性、短事务、故障注入、跨进程恢复、竞争和重复事件由当前测试复核；fixture 准备的合法合成写入与 Runtime 读取分开。不宣称跨库原子性或新增执行授权。

Git 控件复核：没有活动 hook/非 sample hook 文件，17 个候选没有 clean filter，提交签名与 fsmonitor 未启用。独立 Reviewer 审查获准源码、固定字段运行证据和 staged 范围；没有独立重跑测试，也没有查看私有原始记录。其要求的先控件检查、异常固定回退、保留项元数据比对、未知提交不重试已落实。

Markdown：16 个本地链接可在保留的当前工作区解析；其中 2 个 F0 溯源链接指向未入库的 E2A/E2B 历史报告，不是运行/测试依赖。初次检查曾将其列为提交外链接，路径存在性核查与独立审阅后限定接受，未改历史文档或扩大清单。仅克隆此 commit 不能解析这两个参考链接，不宣称文档可移植闭包完整。5 条外部链接为 NOT_FETCHED，不声称远程可达已验证。候选空白检查及差异检查通过。

## 完整提交白名单与初始身份

| 路径 | 角色 | 工作区字节数 | G1 文件 SHA-256 |
|---|---|---:|---|
| `src/aegiscae/research/main_runtime.py` | IN_SCOPE_SOURCE | 11828 | `8c35dc30234f6b6e0f72e8147a4384807fc01fa3ce8d8d6cfdc90cee658d7914` |
| `src/aegiscae/research/main_runtime_rules.py` | IN_SCOPE_SOURCE | 18705 | `d91c924e18302eff1d81d5a1e31b237e1fb61dcb4e2138bf3ecfe830d5d6e46f` |
| `src/aegiscae/research/main_runtime_store.py` | IN_SCOPE_SOURCE | 5475 | `2eb67c701d92a53efd4d932adc6d574b286ca96455034ca30d7ee1dffa7b3e02` |
| `tests/architecture/test_af_read_boundary.py` | IN_SCOPE_TEST | 9109 | `2f11ff5561c5b6676c178d2f11cb3c96368eac6417b868e60caa33b8e04f28c7` |
| `tests/architecture/test_forbidden_direct_writes.py` | IN_SCOPE_TEST | 5551 | `ea93e4188a16c1b7c6a33feb52ef080fed1799a581189e7ee118c79d179de656` |
| `tests/architecture/test_package_skeleton.py` | IN_SCOPE_TEST | 5884 | `cbc6356c566dfbb96edd556932edecd43754f7586f02c90757f9acf527e969fe` |
| `tests/architecture/test_research_boundary.py` | IN_SCOPE_TEST | 13053 | `b84bd8532fa01f6d76b002d62806e067d4f6b837f9c0e303bd27e9e37b59bf4a` |
| `tests/architecture/test_main_runtime_boundary.py` | IN_SCOPE_TEST | 3661 | `d86e429203ac80cd5cd06c2111d32a8b935a22ceab695dda341e3a21710c98fc` |
| `tests/integration/m03f1_safe_replay.py` | IN_SCOPE_TEST | 12991 | `56c1e3b2f3653fc2bbb7ee281b15cbe12a3f90c1f31bafa89d3be12cddabc3b8` |
| `tests/integration/m03f1_support.py` | IN_SCOPE_TEST | 4589 | `ea8a265b2374d1ecaa8cec78e7ab4163425b697fc387ae00d4234c04104b790c` |
| `tests/unit/test_main_runtime.py` | IN_SCOPE_TEST | 33135 | `cdd658b8ebfe48e75f4951d532e31224f79cda0748093b62700ce9cd8560582a` |
| `tests/unit/test_main_runtime_privacy.py` | IN_SCOPE_TEST | 8735 | `bcbca3d5e092e2cc1348c8382bf0e032fb0380b8c3922a8142b95edb7804661e` |
| `docs/architecture/M03_F0_PERSISTENT_CODEX_MAIN_RUNTIME.md` | IN_SCOPE_SAFE_DOC | 32216 | `3e98b0d31c57cbf03f0f45863ae6f5534566b17b63e0dea03c5f63c19adfb6e9` |
| `docs/architecture/M03_F1_BOUNDED_CODEX_MAIN_RUNTIME.md` | IN_SCOPE_SAFE_DOC | 10421 | `81040abba8b19fe559da914a69ed8e093ef487f74ecb112b7fa615821e291166` |
| `docs/milestones/M03-F1_DELIVERY_REPORT.md` | IN_SCOPE_SAFE_DOC | 16599 | `f98745acee9bbfe4dba8a8cd8fd87e0105dad5b35fab15ecb5d3d321fb8ca9ca` |
| `docs/milestones/M03-F1-R1_OFFLINE_REMEDIATION_AND_AUTH_AUDIT.md` | IN_SCOPE_SAFE_DOC | 15915 | `c3d84c524c4b3b5a04b5bef89a8e19ecd6a634002fc70528047b5a466157cf43` |
| `docs/milestones/M03-F1-R1-P1_PRIVACY_SAFE_REPLAY_REPORT.md` | IN_SCOPE_SAFE_DOC | 14753 | `c126f864ee517f6e3323c19c6016c4465ef5d9ac82dbd1711e28411ada84842f` |

以上为审查时工作区字节身份；Git 换行规范化后的 staged/commit blob 另行逐个验证，不混同两种字节摘要。

## 保留但不提交

- `docs/milestones/M01-C_SOURCE_DIFF.patch`
- `docs/milestones/M03-E2A_DESKTOP_COMPATIBILITY_AUDIT.md`
- `docs/milestones/M03-E2B_DESKTOP_INTEROP_DELIVERY_REPORT.md`
- `tests/integration/m03f1_auth_probe.py`

上述四项保持原位，提交前复核 size/mtime，未为扩充提交而复制其历史内容。旧补丁、历史会话证据、本地配置、测试工作区、数据库及认证材料均不在白名单内。忽略规则保持，未访问真实 CAE 模型或修改 AbqJobPilot。

回执生成前，tracked 工作区及 index 为空，剩余 4 个原有未跟踪项；生成本回执后预期为 5 个未跟踪项。最终状态在工具收尾中复核。新隔离测试材料留在仓库外受限目录；没有清理旧材料。pytest/runner 已正常退出，无 App Server/AF 服务需要关闭。普通子进程正常收尾不证明异常 Windows 派生进程树回收。

## CP1-01～CP1-12

| ID | 结论 | 证据及边界 |
|---|---|---|
| CP1-01 | PASS | main、冻结基线、原 4/17 清单及空 index 独立核对。 |
| CP1-02 | PASS | 固定 17 文件闭包，回执明确在提交外。 |
| CP1-03 | PASS | 原 Main/会话/私有 manifest/旧 patch 内容未读取或入库；获准候选报告仅限定投影。 |
| CP1-04 | PASS（限定投影） | 报告证据在输出前白名单过滤，仅标记/身份/计数。 |
| CP1-05 | PASS | 本轮 P1 隐私门及 15 reject / 1 clean 筛查通过，无原始标识回显。 |
| CP1-06 | PASS | Sidecar、Project 只读阶段及原有持久模型保留，无 schema 迁移。 |
| CP1-07 | PASS | 当前 focused/full 真实结果见上表，跳过如实保留。 |
| CP1-08 | PASS（本地限定） | Ruff/架构/空白/staged diff 通过；2 个未打包本地历史参考，5 remote NOT_FETCHED。 |
| CP1-09 | PASS（独立复核） | 源码、范围、负向行为、运行证据、staged blob 经独立审查。 |
| CP1-10 | PASS | 一个本地 commit，parent 精确匹配，17 staged/commit blob 与差异复核。 |
| CP1-11 | PASS | 无 App Server、外部 ACK、Solver/ODB、AF Owner、依赖安装、AbqJobPilot 修改或 push。 |
| CP1-12 | PASS（保持限制） | F1 PARTIAL；REAL_CLI_ACK NOT_TESTED；AUTH UNKNOWN；WIN_PROCESS_TREE_CLEANUP NOT_VERIFIED。 |

## 剩余风险与 R2A 边界

- 本 Checkpoint 只封存 F1 Offline Baseline，不升级完整 F1 验收。
- AUTH UNKNOWN：未进行新的认证请求或修改认证配置。
- REAL_CLI_ACK NOT_TESTED：未创建、恢复或续发真实 Codex 测试线程。
- WIN_PROCESS_TREE_CLEANUP NOT_VERIFIED：异常进程树回收仍未实证。
- 隐私筛查和提交 intent 是本轮受控单写者审计措施，不是防恶意并发 Git 写入的协议，也不追溯清洗历史。
- 后续仅在另行批准 M03-F1-R2A 后，先只读区分 inference authentication、client/server transport、provider/model entitlement、sandbox/config isolation；不从 AUTH 标签预设根因，不要求粘贴凭据。本轮不开始 R2A 或真实 Turn。

已停止，等待下一阶段架构批准。
