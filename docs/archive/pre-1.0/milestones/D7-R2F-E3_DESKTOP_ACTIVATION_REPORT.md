# D7-R2F-E3 — Desktop Plugin Activation

2026-11-01 · **PENDING_USER_DESKTOP_CONFIRMATION**

本文件是当前进度记录，不是安装或验收 PASS。唯一待解除依赖：用户在官方 Desktop 完成独立 Plugin 安装/选中，并在新 Main 执行已准备的非执行操作单。

## 已完成的安装前冻结

- E2 candidate02 Manifest SHA-256：`036afc76901f24267f8ee59f379994ada54dc4b6aa01c72eb5865a355fcb0b4c`。
- Core Wheel：`aegiscae 0.0.0+d7r2f`，SHA-256 `e6c72f12b33b9bf472436916e2331fcf22c7ffe9483652ef238f25dacb932ce6`。
- AF Wheel：`abqjobpilot_gdcae_internal 0.0.0+d7r2f`，SHA-256 `fc2d3e486c5dd3e00f4be08cc57b2a43521d9eacb4480b2da6d23f5083282435`。
- Plugin：`gdcae-d7 0.1.0-alpha.6-d7r2f`，ZIP SHA-256 `5e4959c426f84331bb98a9f360d5703f564808a0906e77cea6566ebc35b15920`；精确 11 个文件与 ZIP、Manifest、env02 内嵌资源一致。
- 当前 GD 68 个来源文件和 AF 123 个来源文件全部与 Manifest 一致。GD HEAD `a75a614f9738af8f257fd490ceec2df4c012ea19`；AF HEAD `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`。未重新构建、安装 Wheel 或使用 checkout 替代候选。
- 复核 env02 的实际发行包 RECORD、版本及只读 `qualified()` 通过；旧共享 Core 没有替换。
- 旧 `gdcae-preview/gdcae/0.1.0-alpha.5` 缓存 12 个文件及原有插件设置已做只读摘要基线；没有打印或复制全局配置内容。新身份没有缓存/设置冲突。

## 已准备的独立入口

任务目录：
`C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-R2F-E3-20261101-A01`

其中 `workspace/plugins/gdcae-d7` 仅来自冻结 ZIP，`.agents/plugins/marketplace.json` 的独立名称为 `gdcae-d7-e2`，显示名为 `GDCAE D7 E3 Acceptance`。没有编辑官方缓存或写用户启用配置。新 Main 操作单为 `workspace/E3_MAIN_ACCEPTANCE.md`；输出目录为 `workspace/acceptance-evidence`，科研状态只允许新建在 `workspace/research-preview`。

官方本地 marketplace 将插件交给 Desktop Plugins Directory 安装。安装后的实际执行来源应为官方 cache，不能用工作区解包副本替代；官方 UI 可能写用户启用设置。[官方说明](https://developers.openai.com/plugins/build/plugins)

## 独立结果（当前）

| 结论 | 状态 |
|---|---|
| PLUGIN_D7_INSTALLED | PENDING_USER_UI；尚未检查安装后的缓存 |
| PLUGIN_D7_ACTIVATED_IN_DESKTOP | PENDING_USER_UI |
| MAIN_V2_ENTRY_VERIFIED | NOT_RUN；当前开发 Main 未代跑 |
| CORE_AF_SOURCE_MATCHED | PREFLIGHT_PASS；新 Main 的实际加载证明仍待取得 |
| NO_REAL_GRANT_OR_OWNER_OR_SOLVER | 当前准备阶段零执行；新 Main 的业务后置检查仍待取得 |
| LEGACY_PLUGIN_UNCHANGED | 安装前基线已冻结；安装后待比较 |
| PLATFORM_ROLE_ATTESTATION_UNVERIFIED | 保留，不重新委派或调查角色身份 |

实际用户操作次数：已发出 **1 轮**官方 UI 操作请求；用户实际完成的步骤数/点击数尚未收到确认，不计为成功。

本轮没有运行自动化测试。E1 防护和 E2 精确三文件白名单保持不变。新 Main 的直接产品操作必须明确记录 `e1_automated_guard_active=false`，不得把 Desktop 业务结果冒充 E1 防护测试；任何自动化测试扩展仍须遵循已有门槛。

安装后将仅核对目标缓存、原插件摘要、该新工作区回执与只读数据库计数。禁止 Owner 生命周期、真实 A/B、Grant、系统权限变化、Stable 操作或 Git 推送。历史事故及全部 BLOCKED/UNKNOWN 材料继续保留。
