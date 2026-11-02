# D7-R2F-E2 — Integration Qualification

2026-11-01 · **D7_R2F_E2_READY_FOR_PLUGIN_ACTIVATION_REVIEW**

限定结论：安装候选、已安装 CLI 的非执行业务入口及纯函数解释器选择通过。未安装/激活 Desktop 测试 Plugin，未启动 Owner，未取得真实人工执行批准，未运行 Solver。历史 R2F BLOCKED 和自定义角色身份阻断不被本结论改写。

## 候选与实际安装身份

唯一推荐候选为任务目录中的 **candidate02**；candidate01 和 env01 的失败记录完整保留，不能按相同版本号互换候选。任务目录：

`C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-R2F-E2-20261101-A01`

[候选 Manifest](C:/Users/wuxia/AppData/Local/Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/GDCAE-D7-R2F-E2-20261101-A01/candidate02/D7-R2F-E2_CANDIDATE_MANIFEST.json) 的 SHA-256：`036afc76901f24267f8ee59f379994ada54dc4b6aa01c72eb5865a355fcb0b4c`。

| 产物 | 精确身份 |
|---|---|
| GD Core Wheel | `aegiscae 0.0.0+d7r2f`；180055 bytes；SHA-256 `e6c72f12b33b9bf472436916e2331fcf22c7ffe9483652ef238f25dacb932ce6` |
| AF Wheel | `abqjobpilot_gdcae_internal 0.0.0+d7r2f`；380671 bytes；SHA-256 `fc2d3e486c5dd3e00f4be08cc57b2a43521d9eacb4480b2da6d23f5083282435` |
| Plugin ZIP | `gdcae-d7 0.1.0-alpha.6-d7r2f`；16239 bytes；SHA-256 `5e4959c426f84331bb98a9f360d5703f564808a0906e77cea6566ebc35b15920` |

来源为 GD main `a75a614f9738af8f257fd490ceec2df4c012ea19` 和 AF Develop `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88` 的实际工作树。Manifest 逐文件冻结当前覆盖层，不能把 HEAD 当作未提交改动的完整身份。全部生产 Python 路径均属于已有 R1 清单；GD 68 个来源文件（46 Python + 两版各 11 个 Plugin 资源），AF 123 个（119 Python + 四份 locale JSON）。不含测试、历史报告、数据库、Grant、凭据、工程 INP/DAT/ODB。四份角色 TOML 的名称和摘要已核对，不等于原生角色加载证明。

安装至全新 `env02`，`system_site_packages=false`，仅安装上述两个 Wheel，使用 `--no-index --no-deps --no-compile --no-cache-dir`；无卸载或共享环境替换。Python 为 3.12.10。实际 GD/AF import 和 Plugin 入口均位于 `env02\Lib\site-packages`，没有从 checkout 或旧 Core 导入。安装后逐项核验 Wheel 原字节、METADATA 和 RECORD，分别核验 77/128 个带摘要条目（含 pip 安装元数据）。模块内历史 `__version__` 仍为 GD `0.0.0`、AF `0.3.0.dev0`，发行包身份以核验过的 distribution/RECORD 为准。

第三方依赖仅通过隔离环境自己的 `.pth` 只读复用 LangChainEnv，没有写共享环境。实际导入 mcp 2.3.0、pydantic 2.13.4、pywin32 312，入口文件摘要已记录。递归展开 active markers 和 requested extras 后，29 个发行包、1595 个 RECORD 文件核验通过；这不是完全独立的依赖环境。Wheel 无 Requires-Dist，依赖约束由随附 Manifest 和审计记录提供，不能宣传为可脱离现有依赖自动安装的发行包。

## 实际修复及测试

本轮只修改以下仓库文件：

- GD `plugins/gdcae/scripts/candidate.py`、`plugins/gdcae-d7/scripts/candidate.py`：同步一行 D7 路径白名单；仅对 d7r2f Wheel 生成四个空 `__init__.py`。两份打包脚本完全一致；四个派生标记单列于 Manifest/RECORD，Desktop Plugin 仍为精确 11 文件。旧版本打包行为保持不变。
- AF `tests/no_real_grants.py`：在用户明确补充批准后，只增加一份测试文件到 A 白名单；其余防护保持不变。
- AF `tests/test_d7r2f_installed_plugin.py`：9 项安装后入口用例。
- 本报告。任务目录另保存可复核的构建、安装核验、测试启动及只读审计脚本与回执，不纳入候选。

首次候选安装成功，但来源核验失败：缺少包标记形成 namespace package，`__file__=None` 被既有严格检查拒绝。补齐的是 Wheel 包结构，没有放宽 `installed_package`。原候选/env01 保留为 `INSTALLED_CORE_REQUIRED` 失败证据；candidate02/env02 是独立新目录。

独立 Reviewer 在执行前批准精确三文件集合：E1 边界 19 项、原 Owner 选择 8 项、新 Plugin 入口 9 项。使用 env02、`-I -B`、pytest importlib 模式、仅测试目录 sys.path、E1 预收集防护及 P1 私有输出投影，**36 passed / 0 failed / 0 skipped / 0 error**。未执行 B 类原控制测试，也未宣称全仓回归通过。修改的打包脚本、白名单和新测试 Ruff 通过；diff/空白检查通过。

| 门槛 | 实际结果 |
|---|---|
| 安装来源、RECORD、11 文件闭包 | PASS |
| 安装后 Plugin CLI doctor/init-v2/status-v2 | PASS；新 v2 Project、真实冻结合同和 A Candidate，非旧 v1 |
| prepare-a/preflight-a、预算占用、相同请求重放 | PASS；调用安装后的真实准备接口，无验证规则替换 |
| approval-preview、重复预览、decline-preview | PASS；非人工决定；拒绝不退占用：held=1、charged=0、available=1、started=0 |
| 错误包摘要、既有目录迁移、期限冲突、引用篡改、执行命令 | 全部拒绝 |
| 全集合新 Grant/Run | 仅 E1 边界用例产生 2 TEST_ONLY；生产类型增量 0；所有 Run 0 |
| Plugin 业务目录 | Grant=0、Run=0、Receipt=0；没有 Owner/启动意图/Standard Operator 文件 |
| 外部执行尝试 | 0；未调用 Owner、Datacheck、Solver 或 ODB |
| Desktop 激活 / 实际 HIL / 实际输出 | NOT_PERFORMED / NOT_ESTABLISHED / REAL_OUTPUT_NOT_OBSERVED |

这些业务测试使用安装后的 `plugin.main()` 和真实非执行准备路径；未用 Fake 求解结果或合成数值充当执行资格。只有专门的 E1 防护测试使用显式 TEST_ONLY Grant。

## 保留证据、Owner 接缝与剩余条件

原事故 32 数据库、27 REAL_FIXED_STANDARD、1 TEST_ONLY、19 Run、369 文件均保留；闭包仍为 `bbf00777051fcbd497701b72a8146bad3446a545a053c84b3123a1914eda5592`。新候选 212 个归档成员未发现事故路径/身份引用。AF 生产源码闭包仍为 `c870c4f07488443dcdd3742c29a55c861a9e3029bb2a4d49ca48bcdab24cd7a7`；未改生产 issuer、Owner 或派发逻辑。

Route C 实际只读预检选择 `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`，沿用唯一 `ServiceLifecycleManager` Popen 接缝及原 Owner，参数为 `-I -S -B`。Standard/protected 非 Route C 的选择逻辑保持不变，原 8 项纯函数/静态测试通过。实际 Owner 启动、跨解释器 IPC 和收尾仍 **NOT_RUN**；纯函数通过不能替代生命周期资格。

独立 Reviewer 最终结论为 `FINAL_E2_REVIEW_PASS_LIMITED / READY_FOR_PLUGIN_ACTIVATION_REVIEW`。其指出首份依赖审计遗漏 `pyjwt[crypto]`；已保留旧 26 包回执并将其标为不完整，修正版覆盖 crypto → cryptography → cffi → pycparser，最终采用 `dependency-closure-v2.safe.json`。

实际证据：任务目录 `install02.safe.json`、`dependency-closure-v2.safe.json`、`closeout.safe.json`，以及 `gdcae-m03f1p1-e2/installed.safe.json`、`fresh-tests/e1-boundary.safe.json`、`fresh-tests/e2-plugin-flow.safe.json`。首次失败材料和新测试产生的本地凭据留在任务目录；不纳入发布包。

**下一次审批仅需分别裁定：**

1. **正式 Plugin 测试安装/激活**：只使用 candidate02 的精确 ZIP，在一个新的专用测试项目准备本地 marketplace，名称拟定 `gdcae-d7-e2`、Plugin `gdcae-d7`、相对来源 `./plugins/gdcae-d7`。经单独批准后由官方 Plugins UI 安装/启用，并在新对话确认实际加载副本的 11 文件摘要；运行解释器固定 env02。预期官方操作会写用户 Plugin cache 和启用设置，不能声称零用户配置变化；不替换旧 `gdcae 0.1.0-alpha.5`，不手工写缓存。本轮未创建该注册入口、未安装、未点击激活。官方文档支持项目本地 marketplace，同时明确缓存与用户设置影响：[Package your plugin](https://developers.openai.com/plugins/build/plugins)。
2. **TEST_ONLY Owner 单独试验**：先冻结新测试目录、精确候选/解释器/Owner 源码、无 Grant/Run 的配置、一次启动及只读 IPC/安全停止白名单、身份与收尾证据；经单独批准且宿主预检通过后才执行。任何 UNKNOWN 均停止、query-first，不接管历史进程、不自动重试；不能据此授权 Standard dispatch 或真实 A。历史 Job/Owner 的 BLOCKED/UNKNOWN 仍保留。

共享 LangChainEnv 的 Core 仍为 `0.0.0+g3d6`；正式 Plugin 缓存、全局 Codex 配置、系统 PATH、账户/ACL、Stable 均未改。两仓 HEAD 和空暂存区保持原状态，未提交、未推送。本轮在此停止。
