# 安装态科研约定

安装并绑定解释器后，所有操作都经同一 Main 的 `scripts/launch.ps1`。从安装回执取得启动器路径与绑定 SHA256，明确选择仓库和插件缓存之外的科研项目绝对路径。每次查询重新打开项目。响应含可直接显示的 Markdown 以及同源结构化字段。

```powershell
$common = @{Action='agreement'; BindingSha256=$receipt; ProjectRoot=$workspace}
& $launcher @common -Operation new -InputFile $newJson
& $launcher @common -Operation freeze -InputFile $bundleJson
& $launcher @common -Operation propose -InputFile $proposalJson
& $launcher @common -Operation diff -Selector $proposalDigest
& $launcher @common -Operation confirm -InputFile $confirmationJson
& $launcher @common -Operation overview
& $launcher @common -Operation detail -Selector $proposalDigest
& $launcher @common -Operation hint
```

输入文件使用 UTF-8 JSON 及绝对路径。以下是填写规则。摘要均保留返回值中的 `sha256:` 前缀。

**暂定约定的最低输入。** 须先冻结真实的、通过当前 Core 结构校验的工程 Bundle，再指定研究问题、阶段目标、变量及比较逻辑、评价和主张边界、已知缺口与修订条件。尚不确定的科研文本可明确填 UNKNOWN；缺少独立证据时保留空引用并列出 UNKNOWN。仅有自然语言、尚无合格 Bundle 时，new/overview/hint 可以显示项目及“尚无生效版本”，propose 返回 FROZEN_BUNDLE_REQUIRED。不要用示例阈值或虚构制品补齐工程合同。暂定约定经明确科研确认后成为 PROVISIONAL，有效范围仅限其声明。

1. **新建**。新目录须不存在，父目录须存在。输入 `{"name":"Study A","schema":"research-agreement-project-v3"}`。保存返回的项目 ID 和修订号。该选项仅在创建时启用。
2. **冻结工程合同**。输入含 `bundle`、`expected_revision`、`key`。bundle 按 Core 的 ContractBundle v1 定义填写，同一项目 ID 用于 Bundle、Goal、Model 与 Verification。保存返回的四段 `refs`。未知值按各工程合同自身规则处理。
3. **提出科研约定**。每个写请求含 `schema="research-agreement-v1"`、`op`、`project`、`expected_revision` 和唯一的 `key`。首次 propose 的 `base` 为 null；修订时为当时的生效摘要。传入 freeze 返回的完整 `refs`、`standing`（PROVISIONAL 或 CONFIRMED）、`reason`、`impact` 以及 `terms`。此时状态为 PROPOSED。写操作返回该请求生效时的项目修订号，随后有其他操作时须重新查询。
4. **填写 terms**。文本字段是 `question, stage_goal, variable_ranges, comparison, criteria, claim, limits, revision_triggers`。`variables` 是已冻结 Goal 允许的变量类别列表，`unknowns` 是重要未知的文字列表。没有证据时用空 `evidence` 并记录缺口；已有引用使用 Model 合同中声明的 `{"artifact_id":…,"sha256":…}`。核对引用身份仅表明声明一致，科研适用性仍需独立依据。
5. **确认**。通过 diff 核对旧值、新值、理由和影响。研究者明确确认后提交公共写字段、`op="confirm"`、`proposal=<精确提案摘要>`、`decision="CONFIRM_RESEARCH_ONLY"`。同键同请求可安全重放。冲突或旧提案不能切换当前版本。暂定版本仍保留 UNKNOWN。
6. **历史归属**。公共写字段加 `op="attribute", agreement=<约定摘要>, kind="candidate" 或 "result", identity=<标识>, sha256=<内容摘要>`。候选只可登记到当时的生效约定。结果还必须提供 `source_candidate={"identity":…,"sha256":…}`，与此前登记的候选及其约定逐一匹配。即便当前已是 v2，v1 候选的迟到结果仍须指向 v1；未知来源或误填 v2 会拒绝写入。归属只可声明一次，标识为 RESEARCHER_DECLARED。它不验证外部制品真实性或代表执行收据。
7. **重要回复**。查询 hint 获取当前版本、状态及未知。已有 SP 历史比较可显式传 `-AgreementRoot` 将提示附在报告中。不关联项目时会明确提示。科研约定的确认与真实求解授权分开。
