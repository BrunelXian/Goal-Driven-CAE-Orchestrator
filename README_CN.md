<div align="center">

<img src="docs/vericae/images/vericae-logo.svg" alt="VeriCAE — finite-element mesh and verification mark" width="96" height="96">

# VeriCAE

**可验证、目标驱动的 CAE 科研智能体**

*从科研问题出发，形成有证据支撑的工程判断。*

[English](README.md) · **简体中文**

[![Project — Research Software](https://img.shields.io/badge/Project-Research%20Software-386597)](product/vericae/vericae-research/README.md)
[![Workflow — Goal-Driven](https://img.shields.io/badge/Workflow-Goal--Driven-237468)](ENGINE.md#research-decisions)
[![Runtime — Codex Native](https://img.shields.io/badge/Runtime-Codex%20Native-70599C)](ENGINE.md#connection-and-recovery)
[![Interface — MCP](https://img.shields.io/badge/Interface-MCP-286E86)](product/vericae/vericae-research/references/mcp-runtime-verification.md)
<br>
[![Release — v1.0.0](https://img.shields.io/badge/Release-v1.0.0-365E94)](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/tag/v1.0.0)
[![License — Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-96536E)](LICENSE)
[![Execution — AbqJobPilot](https://img.shields.io/badge/Execution-AbqJobPilot-97562F)](https://github.com/BrunelXian/AbqJobPilot)
[![Solver — Abaqus](https://img.shields.io/badge/Solver-Abaqus-75612A)](docs/vericae/INT-001.md "历史 Abaqus 轴向杆核验")

[正式下载](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/tag/v1.0.0) · [文档索引](docs/README.md) · [浏览公开源码](product/vericae/)

</div>

## 1. VeriCAE 是什么？

VeriCAE 是面向计算工程的开源 AI 科研框架。研究者不必预先规定每一个仿真步骤，而是从科研目标出发，由 VeriCAE 协助组织科研团队、提出科学假设、规划数值实验、审查模型、分析证据，并决定下一步研究方向。

三个核心原则：**Verified-Model-First**（从针对研究问题完成资格评估的模型出发）、**Goal-Driven**（目标与约束驱动）、**Verifiable**（以证据与独立审查支撑科学结论）。

### 可以开展哪些研究？

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/vericae/images/research-applications-dark.svg">
  <img src="docs/vericae/images/research-applications-light.svg" alt="四类科研应用：材料参数反演、仿真驱动的科学探索、工程设计与工艺优化、物理机制与敏感性研究。" width="100%">
</picture>

上述场景展示框架可以用于规划、组织和验证的研究方向，不代表每个场景均已完成真实求解器的端到端验收。

## 2. VeriCAE 如何工作？

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/vericae/images/research-workflow-dark.svg">
  <img src="docs/vericae/images/research-workflow-light.svg" alt="VeriCAE 工作流：定义科研目标，Main 协调 CAE、Results、Independent Validation，通过受控 MCP 接入 AbqJobPilot，并依据证据形成下一步科研判断。" width="100%">
</picture>

### 科研工作流程

1. **Initiate CAE Research**：明确研究问题、范围、验收准则，建立 Research Contract 与 Research Card。
2. **Conduct CAE Research**：Main 管理科研状态，通过 Task Card 协调 CAE（模型与物理）、Results（结果与证据）和 Independent Validation（独立验证），汇总发现并提出下一步科研判断。
3. **Set Up Research Environment**：需要计算工具时，检查实际运行环境、MCP 可用性及服务身份。

### 双层架构

VeriCAE 使用 Codex Native 持久化角色会话，科研状态保存为 Markdown/YAML 文件，不需要独立的 VeriCAE Runtime 或数据库。Main 是主要科研状态的唯一写入者，角色分工和任务范围属于工作流约束，而不是宿主强制安全沙箱。

[**AbqJobPilot**](https://github.com/BrunelXian/AbqJobPilot) 是独立的 Windows 执行平台，通过 MCP 管理执行授权、作业生命周期和执行证据。Research Contract 不等于执行 Grant。

*上图为目标科研工作流示意，并非已完成的端到端真实求解运行截图。*

历史轴向杆案例验证了数值一致性与独立审查；全新真实 Abaqus 求解与结果提取闭环尚未完成端到端资格验证。[技术内核](ENGINE.md) · [工程案例](docs/vericae/ENGINEERING-CASE-STUDY.md) · [兼容性与验证范围](docs/COMPATIBILITY.md)

### 仓库结构

```text
product/vericae/
├── .agents/plugins/marketplace.json      本地插件市场清单
├── vericae-research/                     Codex Native 科研插件
│   ├── skills/                           Initiate、Conduct、Setup 三项科研技能
│   ├── native-agents/                    三个专业角色的原生智能体定义
│   ├── references/                       科研与角色协作协议
│   └── templates/research-project/       科研工作区模板
├── developer/                            开发工具，用于检查工作区文件
└── release/                              打包工具与发布测试
```

## 3. 安装

VeriCAE 1.0.0 需要支持本地插件 Marketplace 的 Codex。科研规划和离线模型审查不要求安装 Abaqus。

1. 下载 [VeriCAE-1.0.0.zip](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/download/v1.0.0/VeriCAE-1.0.0.zip)，核对 [SHA-256](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/download/v1.0.0/VeriCAE-1.0.0.zip.sha256)，解压至长期保留的目录。
2. 在包含解压后的 `VeriCAE-1.0.0` 文件夹的目录打开 PowerShell，执行：

```powershell
codex plugin marketplace add ./VeriCAE-1.0.0
codex plugin add vericae-research --marketplace vericae-public --json
codex plugin list --marketplace vericae-public --json
```

3. 在 Codex Desktop 打开研究工作区，确认三个 Skill 均为 1.0.0，使用 **Initiate CAE Research** 开始科研规划。

例如：*规划一个悬臂梁端部位移研究，明确参考模型与验收标准，在创建文件前向我展示 Research Card。*

**可选执行平台：** [下载 AbqJobPilot 1.0.0 Windows x64 安装包](https://github.com/BrunelXian/AbqJobPilot/releases/download/v1.0.0/AbqJobPilot-1.0.0-Windows-x64-Setup.exe)。安装包尚未签名。真实计算需要自行提供合法 Abaqus 安装、配置并使用经授权且受支持的执行环境。

[完整安装说明](docs/INSTALL.md) · [兼容性与要求](docs/COMPATIBILITY.md) · [无需 Abaqus 的离线数值复算](docs/vericae/demo/README.md)

## 4. 开发者与贡献

<p align="center">
  <a href="https://github.com/BrunelXian">
    <img src="https://avatars.githubusercontent.com/u/43325767?v=4&amp;s=120" width="72" height="72" alt="BrunelXian"><br>
    <strong>@BrunelXian</strong>
  </a><br>
  VeriCAE 创立者、系统架构设计者与维护者
</p>

ChatGPT 与 Codex 辅助开发，科研方向和验收审查由维护者负责。

欢迎贡献、独立复现及科研合作。VeriCAE 使用 [Apache-2.0](LICENSE) 许可证，AbqJobPilot 使用 MIT 许可证。

## 5. 未来计划

![图 03 — OpenAI Codex 已支持，DeepSeek Harness 与 Google Antigravity 正在适配，Claude Code 与 Grok Build 已列入计划。VeriCAE 通过 AbqJobPilot 连接 Abaqus，并计划通过 AnsJobPilot 连接 Ansys、通过 COMSOL MCP Agent 连接 COMSOL Multiphysics。](docs/vericae/images/ecosystem-roadmap.png)

*VeriCAE 持续演进的生态涵盖智能体宿主、科研编排、执行平台与 CAE 求解器。*

以下为后续工程与科研方向，并非 1.0.0 已完成的功能：

- **自主数值实验：** 完善通用执行环境绑定、全新真实求解任务及独立结果验证。
- **仿真驱动的科学发现：** 探索科学假设、尺度律、无量纲关系、反例搜索及有预算约束的实验选择。
- **材料与制造科研：** 小冲杆和拉伸实验反演、工程优化与增材制造工艺研究。
- **多求解器与多物理场：** 探索更多 CAE 后端，以及可验证的热力耦合与流固耦合工作流。

[科研议程](docs/vericae/RESEARCH-AGENDA.md) · [当前验证范围](docs/COMPATIBILITY.md)

### 科研项目

与 VeriCAE 的开发和科研应用相关的项目。各项目在自己的仓库中维护科研进展与验证状态。

| 项目 | 研究方向 |
| --- | --- |
| [**RL-LAM-ScanOpt**](https://github.com/BrunelXian/RL-LAM-ScanOpt) | 激光增材制造：扫描路径优化、LDED 基准与有限元教师数据。VeriCAE 的目标应用方向。 |
| [**SP-InvOpt / SMALL-PUNCH**](https://github.com/SHUAIXSYU/SMALL-PUNCH) | 小冲杆试验反演：通过力–位移曲线识别材料本构参数。此前的 GD-CAE 与 AbqJobPilot 工作流已为该研究提供支持。 |

此处为关联科研项目入口，不表示均已通过 VeriCAE 1.0.0 的端到端资格验证。其他科研项目公开后将陆续加入。
