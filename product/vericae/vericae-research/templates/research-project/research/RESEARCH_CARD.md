---
schema_version: 1
project_name: ExampleResearch
revision: 1
phase: PLANNING
main_writer: ExampleResearch Main
model:
  path: models/SANITY_MODEL_SPEC.md
  version: M0-DRAFT
  qualification: UNVERIFIED
references:
  - path: README.md
    sha256: 'a2f0bdc306e7ccd516c38e58b04f59128a9370bc12788be1fd0a207e2a4a6576'
  - path: research/TASK_CARDS.md
    sha256: 'b88036208db09c20eaf9f0dba9381f9a6ac4ecf5a2ce707e5f1fa3ed28601de3'
  - path: models/SANITY_MODEL_SPEC.md
    sha256: '3f3ae6aeebf635ad0b83ea44e0c8a10c3319847d051ac0becc7c024e1c321c57'
  - path: docs/initiation/HANDOFF.md
    sha256: '4aacc06db55502a465599a70ed1db9326316371c39d7a261b6a11c11d949beef'
  - path: .abqjobpilot/link.json
    sha256: 'f83701780871b75120b9d11c58051e8faf3791410417d1663c9ce31f25a4c892'
receipts: []
---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚛️ CAE Agent · Research Workspace

**ExampleResearch（模板名称）**　`Draft 01`　`Planning`

### ❶ Research Contract

> **研究命题**
>
> 待 Main 根据实际资料明确研究问题、目标量、评价标准和允许探索范围。

**基准模型**：M0-DRAFT；完整模型定义保存在 [Sanity Model Specification](../models/SANITY_MODEL_SPEC.md)，尚未建立有限元输入或取得研究用途资格。

**研究交付**：待明确；本模板仅提供研究记录结构。

`研究方案草案`　`文件工作区模板`　`尚未执行计算`

### ❷ Research Assumptions

**已提供**：仅有模板与目录规范，尚无实际研究材料。

**暂定假设**：无；不默认材料、几何、分析类型或载荷。

**待确认**：研究目标、模型定义、单位、观察量、评价标准和实际输入。

### ❸ Model Evolution

| 模型版本 | 相对基准的变化 | 状态 |
| --- | --- | --- |
| **M0-DRAFT** | 模型定义占位，尚未生成计算输入 | 🟡 定义待确认 · UNVERIFIED |

*以上仅为模型记录起点；没有已建立或经验证的有限元模型。检查器不验证物理资格。*

### ❹ Research Subagent

| 🧠 **Main Agent** | ⚙️ **CAE Subagent** |
| --- | --- |
| 科研规划、任务分派与主状态单写者 | 工程建模与计算输入检查 |
| ⚪ 待项目 Main 接收 | ⚪ 尚未建立或分派任务 |

| 📊 **Results Subagent** | 🛡️ **Independent Validation** |
| --- | --- |
| 结果读取、分析与短成果回报 | 独立验证与证据审查 |
| ⚪ 尚未建立或分派任务 | ⚪ 按需设置 |

*以上为拟议职责，不证明真实会话存在、通信 READY 或权限隔离；尚未创建 Subagent。*

### ❺ Research Roadmap

- [ ] 🟡 **01 · 研究目标理解** — 尚待实际资料
- [ ] 🟡 **02 · 研究方案确认** — `当前检查点`
- [ ] ⚪ 03 · Initiate → Conduct — Main 核对实际文件并接收交接
- [ ] ⚪ 04 · Sanity Model — 完善模型定义与用途资格证据
- [ ] ⚪ 05 · Research Investigation — 按任务范围研究，执行事实另行核实

### ❻ Next Action

> **Main 接收后先明确研究问题，并核对交接文件引用的实际研究资料。**
>
> 当前没有执行请求。文件状态、描述字段和本地检查 PASS 都不授予执行权限。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 💬 Codex · 工作回复

这是未执行的研究模板。任务见 [Task Cards](TASK_CARDS.md)，交接入口见
[Handoff](../docs/initiation/HANDOFF.md)。模型、任务、研究状态由 Main 按实际证据更新。
真实执行权限和 Receipt/Run 事实仍须通过 AbqJobPilot 核实，本地校验不能认证它们。
