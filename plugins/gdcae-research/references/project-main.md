# 安装对话移交与 Research Main

先从用户已经提供的信息提取研究问题、变量、比较条件、评价指标、资产引用、约束及 UNKNOWN。根据研究主题给出简短工作标签，例如材料反演用 InvOpt。安装对话只组织交接。已接到交接的新 Main 直接进入下节，不再次创建 Main。

1. 从本次 Host 的正式接口取得当前保存的 Desktop Project 身份及 hostId。只使用用户指定或可唯一核实的项目。只有 Host 允许且用户已授权创建独立对话时才能创建；如 Host 要求明确请求，新用户可一次表达“启动这个科研项目并创建独立 Main”。项目名称不需单独审批。
2. 使用安装目录的 scripts/main-handoff.ps1。先按交付清单的独立 manifest pin 验证 package-manifest.json，再按该清单核实脚本自身。每次传入 -HostId、-ProjectId、-ManifestSha256。先 inspect。已有 VERIFIED 时核对既有引用的 Host 身份、项目与标题，再直接返回。已有 UNKNOWN 或未完成交接时只按已有记录对账，禁止再次创建。该版本每个本机用户配置、每个保存的 Desktop Project 只绑定一个 Main。多个研究需要分别明确项目身份。
3. 明确支持 create_thread、读取回执、核对项目及会话时，执行 -Action claim -Title 'InvOpt Main'（名称随项目变化）。仅当本次返回 may_create=true，使用 create_thread，以精确的项目 ID、local 目标、该标题及最小上下文新建同级可见对话。首条消息含请求标识、研究问题表、已有引用、UNKNOWN、能力/许可状态，标明已交接、禁止再次分派 Main。不得转发历史、私有目录清单、授权或凭据。未经允许不打开资料或创建持久项目。
4. 对 ready 回执，将真实 threadId 用 -Action record -RequestId … -ThreadId … 写入。同一 host 定向 read_thread / wait_threads 核实新 Main 已复述目标及 UNKNOWN。按 list_threads 的项目身份或其已保存项目的唯一工作目录和 hostId 核实归属及标题。核对完成才用 -Action verify 加入 -ObservedProjectId 和 -ObservedTitle。工具缺失或不允许创建时返回 BLOCKED_HOST_MAIN_CREATION 和可直接使用的摘要。请求已发出但只有排队客户端 ID、超时、项目/会话身份不明时保留 CREATE_UNKNOWN 或 REF_RECORDED，禁止重发、改名其他对话、切换执行通道或后台冒充。成功后安装对话只给出 Main 引用并结束。

## Main 首轮与后续评估

首条回复先展示科研问题表。区分已有事实与假设，分别列出目标、变量、固定比较条件、指标、证据引用、约束、待确认项。然后说明资产为已有、明确没有或未知。已有模型先评估用途与证据，无模型则给出最小候选设计。例如 Small-Punch 可提出试样/冲头/夹具、材料曲线、夹持与接触、位移加载和力–位移输出，列出需要独立试验、网格敏感性和单位核对的条件。将建议标为建议。在没有 Python 或项目时也要展示表格和下一步。

按随包 sanity-model-protocol.md 的 L0–L5 逐项列事实、推断、UNKNOWN 和建议。用工具可发现的 AbqJobPilot/Abaqus 接口及可读入口元数据说明本机能力；仅在任务需要时检查指定范围。安装、版本或许可证的声明不能证明实际授权。CAE 原生检查须先说明对象范围、脚本来源、许可证、临时写入和副作用并取得授权。按 AOO 分工，只有能绑定真实项目、角色、允许工具及读取可验证结果的 Host 才可启用 CAE、ODB/Results 会话。普通 create_thread 无角色/权限回执时返回 BLOCKED_HOST_ROLE_BINDING，Main 保留任务与证据缺口，不启动代理。产物仅凭项目、角色、任务、来源及摘要匹配后纳入 Main 审查。

## 保存研究层记录

没有冻结合同时，已有 v3 项目可用只读 sanity-triage，输入 schema、op、use、availability、asset_file、concerns、result_scope。结果标注 persisted=false，不要求用户虚构基准或提交模型。尚无 ResearchProject 的 Main 直接开展讨论，确认持久化需求后再使用已有 new 流程。

用户要求保存时，使用 research-agreement.md 中已有 v3 项目与冻结合同。新会话本身不创建项目或授权。安装态 scripts/launch.ps1 接受 -Action agreement -BindingSha256 … -ProjectRoot … -Operation sanity-assess -InputFile …。输入包含 schema=research-sanity-v1、op、project、expected_revision、唯一 key、冻结时返回的 refs、use（指定用途）、availability（EXISTING/NONE/UNKNOWN）、asset_file（用户明确提供的同目录单文件名或 null）、concerns（可含 material、bc、region 等模型字段）、result_scope（NONE/UNREVIEWED/OUTSIDE_USE）。每次重新观察实际字节，禁止自行提交 observation。禁止跟随 include、执行脚本或用文件名判定模型。

overview/hint 返回当前合同的最新资格、缺项与下一步，detail 另含候选引用。换合同后重评。资格待证时可继续讨论和另行授权的探索。QUALIFIED 在本版仅用于 synthetic-axial-compliance-mm-N-v1 的精确解析基准。Small-Punch 实际研究须取得与其用途匹配的独立资格证据，当前适配器不会授予该资格。

候选按原 agreement 的 attribute 登记后，使用同一 launcher 的 sanity-reference。输入公共字段 schema、op、project、expected_revision、key、refs，另给 use、assessment（精确资格回执）、candidate（已登记候选身份）。返回绑定的基准版本及候选摘要；资格不传递给候选。
