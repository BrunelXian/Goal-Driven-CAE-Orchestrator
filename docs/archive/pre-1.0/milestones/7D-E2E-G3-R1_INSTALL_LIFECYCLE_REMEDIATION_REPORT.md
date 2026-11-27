# G3-R1 安装生命周期修复交付

2026-10-30。**限定交付 PARTIAL：实现与零子进程测试完成，真实无害进程资格被安全门槛阻断。** 本轮使用用户授予的源码/纯测试例外，不代表解除原 G3 全局停止。

| 状态 | 实际结果 |
|---|---|
| G3_R1_CODE_REMEDIATION | **PARTIAL**；B0 PASS_OFFLINE，原生后端尚未实机资格验证 |
| G3_R1_HARMLESS_PROCESS_FIXTURE | **BLOCKED / BLOCKED_FIXTURE_GATE** |
| G3_R1_FULL_APPLICABLE_REGRESSION | **NOT_RUN**；任务书要求B1清洁收尾后才能进入B2 |
| BUILD_04_INSTALL_ACCEPTED | **FALSE** |
| OLD_ORPHAN_CURRENT_STATE | **UNKNOWN** |
| BUILD_05_INSTALL_AUTHORIZED | **FALSE** |
| REAL_A_READY | **FALSE** |
| PUBLIC_RELEASE_AUTHORIZED | **FALSE** |

## 1. 基线与保护范围

重新核查：GD `main@69b144cea9aecc515e15cc830368972b09258af9`；AF Develop
`Develop@7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`。两个index均为空。
进入时GD有5项tracked修改、23项未跟踪路径；AF有4项tracked修改，未枚举其无关未跟踪材料。
没有stage/commit/push/reset/clean、AF源码修改或Stable访问。

历史G3、R0报告通过限定字段及摘要读取，旧控制器仅作为静态参考，不导入/执行/改写。
build_04的`installation.safe.json`仍缺失，不补造。旧未知对象没有被查询、接管、猜测PID或终止。
原GD回归 **1269 passed / 1 failed / 21 skipped** 保持历史事实，本轮测试不将它改为绿色。

遵守本机环境登记，使用既有LangChainEnv Python **3.12.10**、pytest **9.1.0**，Ruff **0.12.0**。
无依赖安装、环境变更、pip/wheel操作、doctor、初始化、App Server、AF Owner、Solver、ODB、Grant或系统安全变更。
测试宿主/只读审计/Git/Ruff命令与被测进程家庭分别计数；“零fixture”不表示本轮没有运行测试宿主解释器。

原任务根目录仅从G3报告解析，以下用 `<INCIDENT_ROOT>` 脱敏表示。
新源码及证据位于 `<INCIDENT_ROOT>/r1-lifecycle-01`，下称 `<R1_ROOT>`；没有复用旧安装venv或ResearchProject。

## 2. 实际源码修改

遵照任务书对私有任务控制器的规定，新实现留在受控任务目录；**产品源码、原P1、旧安装控制器和AF均未修改**。
仓库内唯一新增文件是本交付报告。以下六个文件均位于 `<R1_ROOT>/source/`：

| 文件 | 实现职责 | 最终SHA-256 |
|---|---|---|
| `g3_install_controller.py` | 一次性fixture请求、持久账本、严格完成/重复门禁 | `aecbb3787f0885d7473635c250fec427e318d02871a11279ec83dc7225c5564e` |
| `test_g3_install_controller.py` | 注入假后端的零子进程契约/故障测试 | `bbd9eccee04b36897bd33ee3cf5f2d8e07528d59f5a309e5fda99608cbd82e73` |
| `g3_install_win32.py` | 安装fixture专用原生Job/原始句柄后端及权限拒绝门禁 | `205e14d26f50bb99885f6909a289ad430c5b9f080c119cc9a58aee286a1af738` |
| `test_g3_install_win32.py` | 纯权限策略、假句柄、AST接线测试；不加载原生API | `28184e750861842fa63bed1dcfe00cd9d8cdadf4f650bcb6010a0a5e4373ec9e` |
| `g3_install_fixture.py` | 固定参数睡眠父/子fixture，未运行 | `b7f5ec4b61e0774188c1c2ca3998d69fe7540ba3e415808db747aaac6844274b` |
| `g3_r1_safe_checks.py` | 测试宿主进程内pytest、禁止操作拦截及白名单计数出口 | `6fc5880687dad1736598a9c881527b2be73dca1846194b30bc93f94d886bf23e` |

这些是任务控制器源文件，不是新增生产执行接口、通用调度器、MCP工具或安装授权API。
没有将未验证后端放入已有产品wheel。

### 持久性与顺序

- 请求包含固定stage、不可变attempt、明确绝对路径、镜像/fixture摘要、cwd/output、deadline和最多3个范围内进程。
  原生后端另外固定登记中的基础Python路径及SHA，fixture限于同目录已冻结文件，工作目录限于新任务的`fixtures/family-*`。
  不能靠传入任意文件的新摘要让原生后端执行它。
- 独占`attempt.lock`和SQLite账本，短事务、`synchronous=FULL`、显式连接关闭；无数据库事务跨CreateProcess/wait/清理。
  创建前持久记录`ATTEMPT_CREATED → SCOPE_PREPARED → SPAWN_INTENT`。
  原生接口设计为创建时Job关联且挂起，随后提交`ROOT_REGISTERED → RESUME_INTENT`才调用resume。
- 私有账本保留有序事件和摘要链，校验原请求、marker、事件顺序、身份及计数单调性。
  摘要不提供对可改写数据库主体的防篡改认证。
- 进程句柄/Job句柄只属于活owner对象，不序列化数值作为恢复能力，不调用OpenProcess按PID接回。
  重开未完成、UNKNOWN或冲突请求一律拒绝；同一输出根不能借新attempt静默重试。
  完成请求只在原身份、账本和不可变回执一致时重放结果。
- `STAGE_EXIT`、`ROOT_HANDLE_EXIT`、`OWNED_SCOPE_ACTIVE`分开；root exit0而active>0不能成功。
  未取得观察的计数为null，不写虚假的active=0。
- 主失败和收尾失败分别保存。晚期审计写失败不重新执行进程；尽力保存错误、保留此前已提交意图。
  公有回执发布失败保持BLOCKED；强制崩溃/持续写盘失败允许非终态/UNKNOWN，不能承诺总有最终回执。

### 原生后端的实现与未验证范围

实现了原始匿名Job、创建时Job-list属性、CREATE_SUSPENDED、恢复前成员/镜像/创建时间检查、原始root/job保留和Job accounting。
仅设置最多3个活动进程的限制；没有KILL_ON_JOB_CLOSE、breakaway、普通Popen后补加入或失败后不受控降级。
关闭成功的句柄立即清空；后续关闭失败不会再把已关闭数值当作有效句柄。
超时清理代码仅面向经过证明的新fixture原始Job，受本地deadline和明确范围约束，不能操作旧对象。

以上均为**源码和假后端验证**。本轮没有调用实际创建Job/创建fixture/恢复/终止Job路径。
Win32 ABI、创建属性、嵌套宿主限制、真实breakaway拒绝、退出/会计一致性及超时终止尚未资格验证。

Microsoft文档说明Job的默认子进程关联与breakaway条件，但这不能推广到任意broker创建的进程。
源码选择创建时关联也不自动证明当前宿主允许它。
参考：[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)、
[UpdateProcThreadAttribute](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute)、
[Job accounting query](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject)。

## 3. B1 为什么阻断

对**新任务根目录**进行了限定Get-Acl只读观察，不输出SID/账户名，不修改权限，不查询其他账户或全机进程。
观察结果：owner匹配当前主体；除了当前用户、SYSTEM和Administrators，存在3条无法在本轮界定的其他主体继承Modify许可，以及2条应用/能力主体的FullControl/继承许可。
其中一条额外主体许可还包括删除子项。当前证据不足以证明私有账本和源码的访问/完整性边界。

这是**准入条件未满足，不是新进程失控或已发生泄露的证据**。
新增纯SDDL策略会拒绝未知Allow、特殊/回调ACE等；原生入口把该根目录检查放在创建空Job之前。
但这个根DACL语法检查仍不能独立证明祖先目录的DeleteChild能力、有效组访问或源码校验到执行之间的完整性。
不能把它当完整OS安全沙箱，更不能因此修改ACL或绕过宿主权限。

独立Reviewer明确作出 **BLOCKED_FIXTURE_GATE**。因此：

- 实际创建的被测fixture family：**0**；被测root/child/descendant：**0**。
- 实际fixture Job、进程/线程句柄、resume、终止操作：**0**。
- 不存在可交付为“原生进程清洁收尾”的证明；只有假后端账本/假句柄测试。
- B1真实父子、延迟子进程、真实崩溃、嵌套Job/breakaway均 **NOT_TESTED**。
- 按任务书B2前置顺序，产品/完整GD无Solver回归 **NOT_RUN**，没有用模拟测试替代。

所有实际测试过程都结束返回；没有出现新fixture失控事件，因为未跨越原生fixture门槛。
这不说明旧build_04对象已退出，也不替代旧收尾证据。

## 4. 真实测试、失败记录与静态结果

### B0 执行顺序

| 执行 | 实际结果 |
|---|---|
| `b0-first` | 测试运行器在收集前受拦截；0 collected，exit3，无被测进程。首次泛化拦截未记录类别 |
| `bootstrap-diagnostic` | 仅pytest import，在全部拦截下完成；不执行用例，不创建fixture |
| `b0-fixed` | 再次0 collected，确认被拦截类别为WIN_DLL，exit3；未发生实际原生fixture操作 |
| `b0-run01` | **93 passed / 0 failed / 0 skipped / 0 errors**；collected93，exit0；禁止操作0；全部六文件前后摘要相同 |

前两次是测试宿主的过宽DLL拦截问题，不称为93项用例中的失败，也不删除它们的回执。
修复后只拦截被测后端的两个原生入口，保留Popen、socket、os.system拦截；pytest自身Windows运行库加载不被冒充为fixture启动。
输出在2MiB限制内抑制原文，仅发布固定计数、已审查文件/测试名称及摘要。这个机制面向已审查测试，**不是任意恶意Python的安全沙箱**；没有改变历史P1。

真正运行的命令如下，私有根使用上述别名代替：

```powershell
$PY = 'D:/XianLab/envs/LangChainEnv/Scripts/python.exe'
# $R1 必须指向本报告定义的既有 <R1_ROOT>，不是任意目录。
& $PY -I -B "$R1/source/g3_r1_safe_checks.py" b0-first
& $PY -I -B "$R1/source/g3_r1_safe_checks.py" b0-fixed
& $PY -I -B "$R1/source/g3_r1_safe_checks.py" b0-run01
```

运行器在同一测试宿主内调用pytest，关闭插件自动加载和缓存，使用新隔离basetemp，并禁止测试创建子进程。
底层测试参数是两个列明测试文件、`-q -p no:cacheprovider --basetemp <R1_ROOT>/b0-run01-temp`。
已有回执拒绝覆盖；以上是实测命令记录，不是批准重新执行的指令。

B0覆盖：持久意图先于spawn；意图写失败不spawn；登记/resume门禁；root先退出而scope活动；计数/退出状态回退；非法命令/路径/模式；假权限拒绝；同请求/冲突/并发；丢失spawn应答；取消；假句柄缺失；晚期审计失败；回执写失败；保留主/收尾双重错误；marker篡改；假DACL拒绝；静态禁止PID接管、无范围fallback及杀Job-on-close。

**明确限制：** 没有直接注入“SQLite COMMIT已经成功，但append调用的ACK丢失”这个精确故障点。
提交后中断、spawn丢答与重复拒绝测试不能说成该点的等价实测。真实控制器强制崩溃、真实句柄遗失与真实breakaway也未运行。

### 审查期间完成的修复

- 明确关闭SQLite连接，避免把连接context manager误当连接close。
- 保留主错误与清理错误；对未观察计数使用null。
- 处理可捕获取消；强制终止仍只承诺保留此前已提交记录。
- 验证root退出状态及范围计数单调性；回退矛盾拒绝。
- 晚期accounting写入失败时，只补记观察，不重新执行进程，避免生成矛盾账本。
- 成功CloseHandle后清空对应字段，避免后续关闭失败导致误重复关闭已释放数值。
- 明确执行镜像、fixture、模式及新任务工作根的原生白名单；增加私有根拒绝门禁。

### Ruff / diff / 隐私

实际执行Ruff：

```powershell
& 'D:/ProgramData/anaconda3/Scripts/ruff.exe' check --output-format json `
  --config 'D:/Projects/Goal-Driven-CAE-Orchestrator/pyproject.toml' <六个精确新Python文件>
git --no-optional-locks -C 'D:/Projects/Goal-Driven-CAE-Orchestrator' diff --check
git --no-optional-locks -C 'D:/Projects/abqjobpilot_dev' diff --check
```

最终新六文件Ruff **exit0、0 findings**；两仓diff检查均exit0；新文件尾随空白0。
六源码最终摘要与93项通过回执一致。限定隐私模式扫描0匹配；其范围和启发式性质不等于绝对无秘密证明。
AF历史Ruff问题未修复，也没有把本轮新代码Ruff结果说成AF全仓绿色。

## 5. 证据与独立复核

`<R1_ROOT>/evidence/`中保留：`entry.private.json`、`image.private.json`、两份早期失败回执、
`bootstrap-diagnostic.safe.json`、`b0-run01.safe.json`、`ruff-first.safe.json`、`final-static.safe.json`。
纯测试生成的SQLite/marker/回执位于各新basetemp下，身份值均来自合成假后端，不能当实际OS进程证据。
没有为旧build_04或未运行的新fixture生成真实进程ledger。

独立只读Reviewer实际核对了新源码、`b0-run01.safe.json`和六个文件摘要，确认93项通过、禁止操作0、真实family0及摘要一致。
Reviewer未执行测试、DLL、进程/token查询、安装或写文件。其结论是：
**B0 PASS_OFFLINE；B1 BLOCKED_FIXTURE_GATE；整体CODE_REMEDIATION=PARTIAL。**
它要求保留祖先/源码完整性、原生ABI/嵌套宿主、breakaway及真实收尾的未验证状态，不把根DACL语法校验当有效权限证明。

## 6. R1-01～R1-17 验收矩阵

| ID | 结果 | 实测证据与限制 |
|---|---|---|
| 01 | PASS_LOCAL | 两仓实际基线/index/tracked核对；无AF无关未跟踪遍历；只新增任务源码/证据及本报告 |
| 02 | PASS_LOCAL | 旧orphan UNKNOWN、build_04 BLOCKED；原停止状态和历史报告保持 |
| 03 | PASS_OFFLINE | 原生固定镜像/fixture/参数/路径与deadline；当前执行边界未获准启用 |
| 04 | PASS_OFFLINE | 假后端证明持久意图/登记/恢复顺序；缺意图零spawn |
| 05 | PARTIAL | 原始句柄所有权与清空实现/假测试通过；真实保留及close未实测 |
| 06 | PARTIAL | 无PID重新附着/无fallback的静态检查通过；实际嵌套Job/breakaway未测试 |
| 07 | PASS_OFFLINE | root exit0与scope完成分离；active>0不能PASS |
| 08 | PASS_OFFLINE | 模拟失败写入账本、公有回执失败不抹掉已提交证据；实际private ACL未资格验证 |
| 09 | PASS_OFFLINE | 预spawn写失败零spawn；后期写失败BLOCKED；持续失败保留非终态 |
| 10 | PASS_OFFLINE | 同根请求幂等/冲突/UNKNOWN/并发/中断拒绝；不声称精确post-COMMIT ACK故障已测 |
| 11 | PASS_OFFLINE | 最终93项纯测试、源码不变、禁止操作0；保留两次收集前运行器失败 |
| 12 | BLOCKED | 未通过私有账本/源码完整性准入；真实root/child family数量0 |
| 13 | PARTIAL | 假active子进程/晚退出/丢scope/崩溃窗口拒绝通过；真实崩溃NOT_TESTED |
| 14 | PASS_LOCAL | 无实际安装、pip、AF、Solver、Grant或账户/ACL变更 |
| 15 | PASS_OFFLINE | 固定公有回执schema、原文抑制、合成隐私测试；无实际PID输出 |
| 16 | PARTIAL | B0 93通过、Ruff/diff通过、独立复核；B1阻断故B2完整回归NOT_RUN |
| 17 | PASS_LOCAL（限定交付） | 本报告、六源码摘要、真实0进程范围说明和下一阶段拒绝/申请条件；无commit/push |

## 7. build_05 准入申请：NOT_READY / NON_EXECUTABLE

本轮没有创建build_05、安装新包或签发安装许可。以下固定输入只用于后续核对，不能替代尚缺的B1/B2资格。
对历史build_04的两个精确wheel只读重算摘要，并与其SHA256SUMS一致：

| 输入 | 固定SHA-256 |
|---|---|
| `aegiscae-0.0.0+g2long-py3-none-any.whl` | `8c518c9faf5888b41ed5bd235f9d443d6b55e6963f9f556c4d2fdc97d368e01f` |
| `abqjobpilot_gdcae_internal-0.0.0+g2long-py3-none-any.whl` | `648f84984ecb7ecd423f545bc33513e843102ea80622cf46be293358ce7b08cf` |
| 新控制器/后端/fixture | 第2节三个精确源码摘要；未装入上述wheel |

**最小下一步申请：** 先提供或批准限定核查一个已具备适当权限的全新任务根及源码祖先路径，澄清当前额外写入主体的授权关系；不要求用户公开SID/凭据。
如必须改变权限，应先形成另案精确授权，不能把本轮只读权限检查解释成ACL修改批准。
在Reviewer确认完整路径/源码/账本边界后，重新冻结输入，按原顺序执行一次新的无害family B1；洁净收尾后再跑B2获准回归。

只有B1/B2和最终review通过，才提交新的、**单次build_05安装GO**：精确新根/venv/attempt/stage、固定镜像与两个wheel、deadline/范围上限、私有账本/公开回执、原始句柄清理政策及重复拒绝必须完整。
上述wheel是候选输入身份，不是一个已获验收的build_05包。没有资格结果时不能申请直接越过安装门槛。

旧对象的残余风险须由用户单独裁定或独立Operator另案处理；新family通过绝不补造旧证明。
独立Operator实际隔离、真实动态Standard派发和真实DAT来源资格仍是实际A求解前的独立门槛。
本轮停止等待评审，不自动继续B1、B2或build_05。
