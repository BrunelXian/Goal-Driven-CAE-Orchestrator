# G3-R0 安装收尾只读诊断

日期：2026-10-30。本报告是本轮唯一新增文件。没有修复源码、运行测试、重跑安装或查询运行中进程。

| 必需标签 | 结论 |
|---|---|
| G3_R0_BOUNDED_READONLY_DIAGNOSTIC | **PASS：限定诊断完成**；不代表找到存活进程或证明其原因 |
| GLOBAL_STOP_RELEASED | **FALSE** |
| ORPHAN_CURRENT_STATE | **UNKNOWN** |
| BUILD_04_INSTALLATION_ACCEPTED | **FALSE** |
| G3_FULL_REGRESSION | **NOT_GREEN** |
| REAL_A_READY | **FALSE** |
| G3_R1_REMEDIATION | **PROPOSED_ONLY** |

## 1. 结论与证据等级

**SOURCE_STATIC：已确认控制器存在进程生命周期记录缺口。** 它先创建子进程，再登记内存对象；用后台轮询收集派生进程的 PID/创建时间；没有保留派生进程原始句柄或建立 Job 容器。阶段结果与进程观察均先存内存，只有收尾断言全部通过才写最终回执。断言失败时，没有独立故障记录或 finally 路径保存这些观察。因此，历史报告中的失败路径与目前缺失的安装回执在源码上相符。

**UNKNOWN：尚不能确认当时存活对象的准确身份、所属阶段、可执行程序、存活原因或当前状态。** 不将这些静态缺陷等同于“该进程为何存活”的已证实根因，不猜测为 pip、Python 重定向器或某个第三方程序，也不反向声称一定是误报。

本报告使用以下等级，避免混淆：

- **OBSERVED**：本轮对指定静态文件、摘要、存在性或 Git 元数据的直接只读观察。
- **OBSERVED（历史报告转述）**：G3 交付记录中的当时观察；本轮没有原始进程对象/阶段审计重新佐证。
- **SOURCE_STATIC**：当前控制器及相关函数的文本/AST事实，没有 import 或执行这些被检查模块。
- **INFERRED**：由上述事实支持的风险或可能路径；不归因到某个实际进程。
- **MISSING**：指定位置缺失，或控制器设计没有持久保存的证据。
- **UNKNOWN**：现有授权和证据不能回答，不通过扩大扫描补齐。

## 2. 范围、身份与现有证据

唯一事件根目录从原 G3 交付报告的指定段落在内存中解析，下文统一记为 `<INCIDENT_ROOT>`，不公开系统用户名或完整私有路径。只访问任务书指定的精确文件，以及相关安装 helper、P1 捕获函数和一份 G3 产品测试源码；没有目录递归搜索、会话检索、凭据读取或进程枚举。

根目录 `AGENTS.md` 当前不存在；遵守用户给出的 Python 政策，并重新读取全局环境登记。静态解析采用登记中的 LangChainEnv Python 3.12.10，绝对路径启动、`-I -B`、仅标准库；不安装依赖，不导入控制器、产品 helper、测试或 P1 模块。Git 命令仅为只读 branch/HEAD/index/tracked-diff 元数据，禁用可选锁、外部 diff 和 textconv；未枚举两仓无关未跟踪材料。

**OBSERVED：**

| 仓库 | 当前边界 |
|---|---|
| GD | `main@69b144cea9aecc515e15cc830368972b09258af9`；index 空；5 个已跟踪修改 |
| AF Develop | `Develop@7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`；index 空；4 个已跟踪修改，均属于既有 checkpoint 白名单 |

GD 的五项为 README、Plugin helper、setup Skill、rod_bridge 和 package_skeleton 测试。未查看 Stable；没有将“未枚举无关未跟踪材料”说成对其内容完成全面审计。原 G3 报告、进度、CP 绑定及相关源码保持原样。

### 指定证据存在性与 SHA-256

以下相对路径均在 `<INCIDENT_ROOT>` 下；摘要仅证明本轮读取字节的一致性，不是可信签名，也不能单独证明它们就是历史执行时的字节。

| 证据 | 本轮观察 | SHA-256 |
|---|---|---|
| `product/install_final_04.py` | 存在；125 行；仅静态读取 | `36425b47a3d509c6e1b3e085f83bc875826da15ab6905e5d7b4b25140bbfe9f5` |
| `venv-creation.safe.json` | 存在；声明 PASS_LOCAL、creation_exit=0、未下载外部依赖/修改共享环境 | `856687754cfe3661e227d546ea1379ead5b9eda1bbbd66a997b26c0b7093fe36` |
| `release_candidate/build_04/export.safe.json` | 存在；声明 PASS | `0c9f0a3322b4d33672f658dc848d49ab9c67bcb288a8eed1baece8150eaf81ce` |
| `release_candidate/build_04/closure.safe.json` | 存在；声明 GD57/AF59 文件闭包通过 | `ac8175ee4279b3d39a0c3b8d42488b1fe8441709784c69751d5c8fe0902816d9` |
| `installed research G3/gdcae-package.json` | 存在；execution_authorized=false，Plugin 未测试 | `5bc20f47bbc990411d40ef3fae577168511cc494b77753ac8631726fc02c945b` |
| `installed research G3/gdcae-source-receipt.json` | 存在；commit_inclusion=NOT_ASSERTED、无执行授权 | `cf36474144d916e4b346bbaacdae683bc881c97258b41c4ce146712c0fe54f47` |
| `installed research G3/gdcae-research-init.json` | 存在；声明 revision2、两次预算、A/B NOT_RUN、无执行授权 | `e51d4503ff59772af87823bf3cc5c6c0f7a25b0b38abab86c3dc589783470eed` |
| `release_candidate/build_04/installation.safe.json` | **MISSING**；未创建或补写 | — |

这些是六份不同用途的已有文件，并非六个安装阶段分别持久化的退出证明。没有重跑 RECORD、doctor 或初始化来验证其声明；包闭包与初始化产物存在，不等于安装进程范围收尾成功。

相关当前源码：

| 文件 | SHA-256 |
|---|---|
| `tests/integration/m03f1_safe_replay.py` | `56c1e3b2f3653fc2bbb7ee281b15cbe12a3f90c1f31bafa89d3be12cddabc3b8` |
| `plugins/gdcae/scripts/gdcae.py` | `b966bab40c7ac62739cde6938d929713bdc68317268fb5a17d5c85a77163dde4` |
| `tests/unit/test_g3_product.py` | `398c9917740589d88e86e37fb9a0ce6a6b79c9dbc75c42c4fce6602a025194a2` |
| 原 `7D-E2E-G3_DELIVERY_REPORT.md` | `ea36297d56932c75cf533b064c67bae8f13e7bf1ef7f7ede00db02ca51607f95` |

包内精确 Plugin helper 与当前仓库 helper 字节相同。G3 产品测试源码覆盖 doctor/RECORD、初始化来源及四角色字节，未引用该安装控制器或 Job Object；这项静态观察不推广成“整个仓库没有进程测试”。

## 3. 六阶段与进程关系

控制器 `execute`（51–57 行）统一启动任务 venv 的 Python，带 `-I -B`，cwd 为任务根，捕获输出但不公开原文。六次调用如下：

| 阶段与控制器行号 | SOURCE_STATIC：直接子进程工作 | 对派生进程的结论 |
|---|---|---|
| 58–67 | Python `-c` 查询版本、prefix、pip 元数据和模块存在性 | 脚本未显式启动子进程；不能据此证明运行时无派生对象 |
| 75–76 | Python `-m pip --isolated install` 两个本地 wheel；no-index/no-deps/no-cache-dir/no-compile | 可能涉及安装器或解释器内部行为；确切实际派生关系 UNKNOWN |
| 77–82 | Python `-c` 导入两个包、检查模块来源 | 导入的传递行为未由当前范围做完整运行时证明 |
| 84–89 | 包内 helper `doctor`，检查两个发行包 RECORD | helper 函数无直接进程启动调用；不能据此确定历史对象归属 |
| 90–99 | `init-research`，建立新 workspace、冻结 Project、写来源回执 | 明确文件/数据库写入阶段；R0 没有重复执行 |
| 100–102 | `doctor --workspace`，核对 Plugin/四角色字节 | 非 Desktop 激活或子 Agent 实际加载证明 |

`gdcae.py` 的 `doctor` 为124–155行，`installed_package` 为158–217行，`prepare_workspace` 为67–108行，`initialize_research` 为247–282行。检查到的 helper 没有直接 subprocess/os.system/os.spawn 调用。没有扩展到 pip 内部、全机解释器/启动器或其他用户程序的源码调查，因此不将 Windows venv 启动机制、pip 或任何阶段认定为元凶。

**OBSERVED（历史报告转述）：** 六阶段 exit0、随后收尾断言失败、控制器 exit1。**SOURCE_STATIC：** 若当前所示执行确实到达109行，则前面的六个 exit0 与业务断言门禁均已通过。**MISSING：** 当时逐阶段持久化的过程审计，无法把那个派生对象可靠绑定到某一阶段。

## 4. 生命周期缺陷与证据强度

### D1：创建与登记之间存在缺口

**SOURCE_STATIC，35–39行：** `launch` 先调用原始 Popen，再取得 psutil 对象与创建时间，最后 append 到 `owned`。直接子进程的 Popen 对象在成功 append 后被保留，正常情况下其原始 Windows 进程句柄随对象保持；不是“所有进程都没有句柄”。但在创建成功、元数据读取/append完成之前异常退出，已产生的副作用可能尚未登记。没有持久 start intent，也没有对这段缺口的专门拒绝/故障路径。

### D2：轮询只提供有限观察，不提供完整所有权

**SOURCE_STATIC，40–49行：** 后台 daemon 每10ms从直接子进程的 PID 查询进程，核对创建时间，然后调用 `children(recursive=True)`，仅把派生 PID→创建时间写入内存字典。没有派生对象原始句柄、镜像身份、阶段索引、独立 provenance 记录或 Job Object。

**INFERRED：** 短生命周期、轮询间隔内创建/退出、重挂父链、父进程已结束或停止采样后新产生的对象可能未覆盖。PID+创建时间比单独 PID 更有用，但不是原子身份认证或完整范围证明。不能据此断言此次发生了具体 PID 复用或 psutil 的某种实现缺陷。

监控只捕获 NoSuchProcess；其他异常可能结束 daemon，且没有健康状态传递。103行 `join(2)` 后未检查 watcher 是否真正结束，存在未被否定的观察缺口/并发访问风险。这些是潜在失败路径，不是此次已观察到的线程异常。

### D3：证据在验收之后才落盘，故障反而跳过证据

**SOURCE_STATIC，50–57、103–125行：** stages 与 owned 均为内存集合。收尾先停止监控，再逐项 poll直接子进程、查询已观察派生对象；109行的存活断言位于唯一最终写文件124行之前。没有覆盖整个执行的 try/finally、失败回执或追加审计。第一个收尾异常也会跳过其余对象的检查。

因此可以确认“为何没有持久记录”的实现原因。不能确认“为何该对象存活”的运行时原因。即使走到成功路径，119–120行也只打算保存直接子进程身份和派生数量，无法重建派生对象身份图。124行是最终 `open('x')` 写入，没有显式 flush/fsync 或原子发布协议；写盘中断也是拟议故障测试对象。

**SOURCE_STATIC，125行：** 成功分支会打印完整最终对象，其中包含直接进程标识及私有路径。这是需要修复的潜在输出边界问题。按照历史报告的109行失败路径，该打印没有执行；本轮没有据此报告已发生新的泄露，也未重新执行它。

### D4：P1 输出捕获不是进程树收尾器

**SOURCE_STATIC：** 控制器17–18行导入 P1，34–39行替换其 subprocess.Popen。P1 `_capture` 的117–155行处理原始直接子进程、输出管道、输出上限和超时；使用 CREATE_NO_WINDOW，超时/溢出路径针对原始直接子进程 kill/wait。它没有 Job、派生进程集合或全范围完成验证。

`cleanup_unknown` 是超时、溢出与drain失败的合成标志；false不证明派生范围为空。reader join失败的断言还可能在返回结果前抛出。这里仅分析既有代码，不调用这些终止路径。R1不应通过改写历史P1语义或扩散monkeypatch来掩盖控制器职责缺失。

### D5：当前状态与外部影响仍未知

**MISSING：** 决定性派生身份未持久保存，原始派生句柄未保留，聚合安装验收回执缺失。**UNKNOWN：** 是否仍活着、是否已自然退出、是否发生任务目录外副作用。

当前没有满足任务书要求的精确、可信、持久化身份链，因此完全没有执行运行中进程查询，也没有根据父PID、时间邻近或目录猜测身份。其他AF测试正常收尾、Core回归结束、文件存在均不能替代此事件的证明。

## 5. 同用户与宿主风险

**SOURCE_STATIC：** 控制器29–32行保留包括 PATH、TEMP/TMP、USERPROFILE、APPDATA/LOCALAPPDATA 在内的十个环境键；只增加pip限制和禁写pyc等设置。cwd是任务根，但没有把TEMP/TMP改到任务私有目录，也没有令牌隔离、ACL隔离或进程容器。`-I`、pip isolated、CREATE_NO_WINDOW和路径约束不是Windows安全沙箱。

**INFERRED：** 同用户子进程可能拥有与该用户相同的敏感资产访问能力；临时写入也未必只限任务根。现有证据不能证明发生了秘密访问、网络通信、外部持久化或真实执行；同样不能凭环境白名单证明它们绝不可能发生。R0不扩大到有效ACL、全局配置、环境值或全机进程调查。

## 6. G3-R1 最小施工清单（仅提议）

目标限于安装进程范围和证据闭合，不建设新Agent Harness、服务、AF Supervisor或Solver生命周期。

### 精确建议白名单

| 新文件 | 最小职责 |
|---|---|
| `tests/integration/g3_install_scope.py` | 安装专用范围/原始句柄管理、私有生命周期账本、公有白名单投影 |
| `tests/integration/g3_install_controller.py` | 显式阶段表、失败停止、重复attempt拒绝；R1只接合成阶段，不执行安装 |
| `tests/integration/g3_install_fixtures.py` | 无害、可控、任务专用子/孙进程故障fixture |
| `tests/unit/test_g3_install_scope.py` | 账本状态、幂等、隐私与故障单元测试 |
| `tests/integration/test_g3_install_scope_windows.py` | 获准后验证精确自有Windows进程范围、崩溃与收尾 |
| `docs/milestones/7D-E2E-G3-R1_INSTALL_SCOPE_REMEDIATION.md` | 实际修复、失败记录、测试与下一次GO条件 |

不修改旧 `install_final_04.py`、build_04、历史报告、P1 helper、AF、生产Core/Plugin/F1、账户、ACL或全局配置。白名单若不适合现有结构，应在R1开工前提出精确替代，不静默增加文件。新测试目录仅放新fixture和非秘密账本，保留失败材料；回滚是停止新工作，不删除旧证据。

### 生命周期与持久化

1. **创建之前：** 新attempt身份；固定阶段allowlist及参数摘要；新cwd/temp/output；先以exclusive方式写入并durably flush `START_INTENT`，验证账本可写及边界后才允许产生子进程。记录版本、attempt、stage、来源/可执行文件摘要、单调序号、状态、范围策略；不记录token、全量环境或任意原始输出。
2. **创建时：** 短事务/短文件提交，不跨外部工作持有SQLite写事务。原始子进程句柄持续保留到验证退出，私有记录包含精确创建时间、镜像/来源和scope关系。句柄数值不是可持久化的接管能力；重启后不得据旧PID、名字或账本自动接管。
3. **范围建立：** 候选是任务专用Windows Job，优先验证子进程代码运行前即可归属范围的创建协议。不得采用普通Popen之后才事后加入的“无竞争保证”。若仅能挂起创建→加入→恢复，必须显式处理创建与登记/加入之间的崩溃窗口；证明不了就拒绝真实安装资格。检查宿主已有Job/嵌套限制、权限、breakaway策略和句柄继承；不允许借breakaway绕过宿主约束。
4. **终止策略独立授权：** 不默认启用KILL_ON_JOB_CLOSE，不因用了Job就取得终止权限。没有此策略时，控制器崩溃不等于子进程已退出。无法安全加入范围时禁止恢复子代码/进入下一阶段；如果连获授权的范围内回滚都不能证实，保留UNKNOWN。R1未来测试只允许其fixture owner通过原始句柄/已证明自有范围收尾，绝不操作build_04旧未知对象。
5. **运行中：** 每阶段/生命周期事件追加、排序、及时flush，明确监控健康；记录主失败和收尾失败而不互相覆盖。界面仅输出固定状态、计数、阶段标签及摘要；私有账本与公开回执分离。任务目录不自动称为访问控制安全边界；既有权限不足时拒绝，不擅改ACL。任务私有TEMP与精简环境只算卫生措施，不算隔离。
6. **结束时：** 所有可处理退出路径尝试写终态并关闭自有观察器，逐对象保留失败，不能首个assert就放弃其余账目。强制退出、掉电、磁盘失败时只能保证此前已提交记录，允许留下非终态/UNKNOWN；不得承诺“所有路径必有终态”。
7. **验收：** 同时证明所有阶段结果合格、输出投影安全、原始进程范围完成、观察线程/句柄收尾可验证，才原子发布PASS回执。Job成员/完成记账须有确实验证的完整性，不能用一次pid列表或计数为零冒充。缺句柄、观察器死亡、记录写失败、范围歧义、读管道未完成均阻断。相同未完attempt再次调用必须拒绝，不能静默重装。

## 7. R1 故障注入和 build_05 门槛

下表是未来验收要求，**本轮均未执行**。所有活进程用例仅允许新建无害fixture，禁止以安装器、用户进程或Solver做故障对象。

| 拟议验收 | 必须证明 |
|---|---|
| 正常直接子/孙进程 | 阶段和范围均完成，持久生命周期可关联；无公共原始身份输出 |
| 延迟子/孙进程 | 直接父exit0时不提前PASS；范围完成前阻断后续阶段 |
| 分离/breakaway请求 | 被容器策略拒绝或完整可证明归属；否则UNKNOWN，不放宽宿主权限 |
| PID复用 | 合成身份冲突被拒绝；不得借实际用户进程制造复用，不凭PID接管 |
| intent后、创建前崩溃 | 留下可识别未完attempt，不自动重发 |
| 创建/归属/恢复前后故障 | 无代码抢跑或明确UNKNOWN；覆盖创建到登记缺口 |
| 控制器退出、孩子仍存活 | 私有已提交来源保留；不写安装PASS；由预授权fixture owner精确收尾 |
| 缺句柄/权限拒绝/镜像不明 | 拒绝接管与成功；不扫描全机寻找替代身份 |
| 账本写入/flush/磁盘故障 | 首次意图失败不启动；运行中写失败阻断继续，保留此前提交；不能假造终态 |
| reader join失败、监控线程死亡 | 健康状态进入拒绝门禁，保留原错误与收尾错误 |
| 输出超限、超时、取消 | 只触及明确获准范围；不能静默吞掉仍存活对象 |
| 重复/并发调用 | 一个attempt只有一个owner；未完成或UNKNOWN不重复执行，不扩大预算/权限 |
| 隐私与崩溃输出 | 合成秘密/PID/路径/异常均在输出前白名单拒绝；原始数据不进聊天/报告/CI |
| 严格成功回执 | 禁止只有六个exit0就PASS；完整closeout条件缺一即BLOCKED |

R1通过后仍需**独立的build_05 GO/NO-GO**：先复核R1证据与Reviewer，明确旧未知进程的残余风险是否由用户接受或交独立Operator另案解决；不能用R1新fixture通过解除旧事件。核对固定新包来源、host范围能力、已批准的新任务目录/attempt、私有账本和公开回执边界，单独授权一次新安装。build_04永久保留历史BLOCKED，不重写为PASS。R1不包含真实A/B、Grant、AF Owner、App Server、Desktop激活或发布。

## 8. 独立 Reviewer 意见与落实

使用不同的原生 `gdcae-reviewer` 角色，保持只读。Reviewer没有运行代码/测试/进程查询，也没有独立获取本机原始文件；其依据是Main提供的脱敏行号、AST摘要、源码SHA和证据存在性结果。因此本结论是**对所提供证据和修复范围的独立逻辑复核**，不是第二次独立取证或产品批准。

Reviewer确认：创建到登记的异常缺口、轮询覆盖不足、监控健康未闭合、首个断言跳过后续审计、最终回执迟写，均是摘要支持的源码问题；不能据此归因当时存活对象或判断其当前状态。它明确指出六份现存产物仍在，不能说所有阶段证据都丢失。

Reviewer要求的两项收紧已纳入：只对可处理退出承诺终态尝试；强制崩溃/写失败保留UNKNOWN。Job范围不等同owner崩溃后的清理，不默认赋予终止权。另补充监控死亡、reader join、加入/恢复失败及双重错误故障矩阵。潜在完整回执打印问题标为未执行成功分支，不伪称已发生泄露。

## 9. G3-R0-01～14 覆盖

| ID | 诊断覆盖及边界 |
|---|---|
| 01 | 政策和原报告受限读取；根AGENTS缺失已记录 |
| 02 | 双仓branch/HEAD/index/tracked元数据；无无关未跟踪遍历 |
| 03 | 精确根/控制器/六产物和缺失聚合回执；有摘要 |
| 04 | 六阶段静态调用链；实际派生归属UNKNOWN |
| 05 | 直接句柄与派生PID记录区别、无容器及观察竞争 |
| 06 | 迟写回执/异常路径造成决定性身份缺失的静态原因 |
| 07 | 六exit0、历史存活断言、exit1、当前UNKNOWN分别记录 |
| 08 | 精确身份查询门槛不满足；完全未查询运行进程 |
| 09 | 安装专用范围、私有账本/公有投影最小方案 |
| 10 | 有界无害fixture故障矩阵及权限边界；未执行 |
| 11 | 精确拟议白名单；build_05另批，build_04不改历史 |
| 12 | 不同原生Reviewer逻辑复核及取证限制公开 |
| 13 | 分类结论，G3旧失败及停止状态保持 |
| 14 | 仅新增本报告；无源码、依赖、权限、Git提交修改 |

## 10. 一页决策请求

**建议下一步：批准限定G3-R1源码与合成进程故障测试，不批准安装重试。** 白名单见第6节；R1不得修改旧任务controller/材料，不扩展生产执行权。

拟议需批准的副作用仅为：六个列明新文件、新任务fixture目录/私有账本、短生命周期无害Windows子/孙进程，以及由测试owner对原始句柄/已证实自有范围的限时收尾。不得包含全机扫描或build_04对象终止。无管理员/账户/ACL/服务/全局配置变更；如果Job能力或账本权限在既有上下文不可用，停止相关支线并报告，不提升权限。

可选决策：`APPROVE_R1_BOUNDED_SOURCE_AND_SYNTHETIC_FIXTURES` 或 `REQUEST_REVISION`。任何批准都不解除旧未知对象状态、不接受build_04，不包含build_05安装。旧未知对象若必须调查/处置，需要独立、明确的Operator授权方案，不能以当前丢失身份的账本猜测目标。

G3原完整回归仍为1269 passed / 1 failed / 21 skipped，R0执行pytest数量为0。原有AF收尾与新静态诊断不能证明安装范围退出。真实A仍NOT_READY，本轮结束等待架构评审。
