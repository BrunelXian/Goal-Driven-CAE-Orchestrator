---
name: research
description: "Discuss research goals, review Sanity Models and plan CAE work without Python; use the verified Core for deterministic curve analysis and ResearchProject records."
---

# GD-CAE Research Preview

进入或恢复本插件会话时先处理[版本检查](../../references/update.md)。Hook 未提供本次结果时从实际安装位置执行只读 check。离线、拒绝或暂不更新均继续当前科研任务。

收到明确的新科研任务、已移交的 Main 首轮或基准资格问题时，执行[项目 Main 与模型资格流程](../../references/project-main.md)。已移交的 Main 首先展示问题表，再评估模型资格；安装对话负责一次性交接。

基础模式：直接用中文讨论研究目标、假设和证据缺口，按[Sanity Model 协议](../../references/sanity-model-protocol.md)审查模型，解释 Model Contract 或拟定下一步。该模式无需 Python、绑定、Shell 或数据库，不调用 hint，不生成数值验证或持久化记录。

Core 模式：用户要求实际曲线计算、科研项目读取或写入时才需要已验证的本版本绑定。若无绑定，显示[中文双方案](../../references/runtime-options.md)并等待选择，按[setup](../setup/SKILL.md)完成用户同意与核验。取消后继续基础模式。对 Core 拒绝如实报告。以下指令仅适用于 Core 模式。

For a research agreement, use the same launcher and the [installed agreement commands](../../references/research-agreement.md). Ask which explicit ResearchProject the researcher means. Read `overview`, `detail`, `diff` or `hint` and show the returned Markdown. Never infer confirmation from a query or proposal. Confirm only the exact reviewed digest after an explicit researcher decision. In significant research replies, obtain a fresh hint for that project. For the SP comparison with an associated agreement pass its absolute `-AgreementRoot` to `main`. Preserve the version identity of earlier messages.

For questions about model qualification, variables or scientific acceptance, consult the bundled [Sanity Model protocol](../../references/sanity-model-protocol.md). Distinguish its research guidance from this release's read-only historical comparison. Installation and research agreement confer no solver authority.

Use the installed copy of this skill for the adapted SMALL-PUNCH case on Windows. Obtain the operator's absolute external project root, a fresh output directory outside the project, and the binding SHA256 saved at installation. The parent of the output directory must already exist.

From this SKILL file resolve the plugin directory containing plugin.json. Run its scripts/launch.ps1 with `-Action doctor -BindingSha256 <receipt SHA256>`. After success, invoke the same launcher with `-Action main -BindingSha256 <receipt SHA256> -ProjectRoot <external root> -OutputDirectory <fresh output>`. The receipt identifies an explicitly selected CPython 3.12.10 and this installation. If it is missing, follow the installation guide. On any refusal, report the error and stop.

The verified adapter first reads project instructions, blind protocol and policy metadata. It reads only the exact file list defined by the bundled core module. Keep all results outside the external project. Use the original external project supplied by the operator. Never execute project scripts, open ODB binaries, follow private links or submit jobs.

Use report.json and curve_difference.csv to explain the two material tables, unchanged model cards, public CSV provenance, selector, sampling, signs, interpolation, endpoint, RMS and largest full-curve difference with its location. Distinguish model units from verified physical units. Cite the produced files and the provenance limits. Explain whether the evidence supports accepting the material and propose one bounded next validation in light of the public run_063/run_064 summaries. Disclose prior exposure from the protocol. This single-Main preview has no execution authority. Keep the host-provided skill invocation distinct from driver checks.
