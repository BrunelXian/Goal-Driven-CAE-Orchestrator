# CAE Agent Scoped Fixture 0.0.3

本地 Marketplace 候选包含 `gdcae-core` 与 `abqjobpilot` 两个 stdio 入口。目标为隔离测试测点向下位移 1.0 ± 0.1 mm。逻辑 Main 可保存任务、按观测值推进候选、查询下一步和重新打开研究项目。Classic 0.2.2 从正式项目读取队列与状态。模拟执行使用绑定的 GD-CAE Fixture。

## 安装与一次范围授权

适用于 Windows。本候选实测 CPython 3.12.10 和 MCP SDK 2.3.0。安装人员从本机环境登记选择已有解释器，运行 `& $VerifiedPython -I -B -c "import sys, mcp, win32api, importlib.metadata as v; print(sys.executable, sys.version, v.version('mcp'))"` 核对绝对路径与版本。固定上游服务归档 SHA-256 为 `34bb598048e24dbbe180ea1255227383012f1858579c2f8468cead1ac994d5df`，提交为 `7012133e7cc0176bb3e56fc24d7154ee3b90bb81`。已有 T02 部署可复用此归档。开发环境也可用原部署工具 `product/research-preview/tools/prepare_abq_service.py` 中的 `service_archive(reviewed_repository)` 从固定提交只读导出。准备本机 Classic 隔离项目的根目录、独立核对的 UUID 及其允许读取的队列。本候选不分发供应方代码。

对照交付回执校验 ZIP SHA-256，将 ZIP 解压到本机新的独立目录。以下 PowerShell 变量分别由操作人员指定。使用 Desktop 自带的 Codex 可执行文件，测试选择独立的空 Host 配置目录。所有目录、解释器和后端 UUID 均为本机选择。候选使用独立插件 ID。

```powershell
$env:CODEX_HOME = $IsolatedHostHome
& $DesktopCodex plugin marketplace add (Join-Path $Extracted 'market')
& $DesktopCodex plugin add 'cae-agent-scoped-fixture@gdcae-fixture-lab'
$Installed = Join-Path $IsolatedHostHome 'plugins/cache/gdcae-fixture-lab/cae-agent-scoped-fixture/0.0.3'
$Profile = Join-Path $IsolatedHostHome 'gdcae-scoped-fixture/deployment.json'
& $VerifiedPython -I -B (Join-Path $Extracted 'configure.py') --plugin $Installed --manifest-sha256 $IndependentManifestPin --profile $Profile --provider $ReviewedProviderZip --backend-root $IsolatedBackend --backend-work-root $AllowedInertJobDirectory --backend-id $ExpectedBackendUUID --queue-id $InertQueueId --binding $FreshScopeFile --new-fixture-root $FreshResearchProject --max-executions 3 --ttl-seconds 3600
```

授权入口要求绑定文件与科研项目使用新路径，父目录已存在。授权参数固定 1 CPU、仅 F、最大模拟次数 0–3，真实作业预算 0。配置已有作用域时用 `--binding-sha256 <独立授权回执中的摘要>` 替代 `--new-fixture-root` 等新建参数。配置在独立 Host 目录的 `gdcae-scoped-fixture/deployment.json`，不需要修改系统 PATH。更新版本或部署请重新核对外部清单、绑定与供应方后在新配置中安装。移除绑定文件可立即使后续受控调用失败。请保留已写入的项目和证据。

在启用候选并使用该配置的 Desktop 会话内可请求“在已授权项目中运行位移 Fixture，按返回结果迭代直至终态，并读回任务和证据”。普通 Desktop 路由按实际观测单独验收。独立的 Host 协议取证脚本为 `product/scoped-fixture/host_probe.py`。仓库根目录的 `examples/scoped_fixture/rehearse.py` 用于自动化重跑核心纵切。回执附本轮实测执行面和计数。

已有 Classic 工程可使用隔离队列内的一条惰性 QUEUED 测试记录及其已知标识。配置时核对记录的输入与结果路径受允许的作业目录约束，服务端校验队列摘要和项目 UUID，状态查询只接受登记的记录。首次安装时也可指定新的本地隔离目录，将上面的 `--backend-id … --queue-id …` 替换为 `--create-empty-backend`，通过固定供应方自己的 ProjectManager 创建空项目；运行下方验收时省略 `--queue-id`。该模式调用队列和历史列表，模拟执行仍在 GD-CAE 侧的测试适配器中进行。

## 可复现打包

ZIP 内含安装态验收入口。在新作用域上运行以下命令会实际执行模拟迭代并留下完整回执。Host 取证客户端另使用已核验的 psutil（A 机 7.2.2）观察子进程退出。每次打开都重新启动 Desktop 随附的 app-server；用户账号、认证文件和日常 Desktop 配置不参与此协议测试。

```powershell
& $VerifiedPython -I -B (Join-Path $Extracted 'product/scoped-fixture/installed_case.py') --codex $DesktopCodex --home $IsolatedHostHome --market (Join-Path $Extracted 'market') --queue-id $InertQueueId --output $NewReceiptFile
```

在源码仓库使用已核验的解释器和完整提交号运行 `& $VerifiedPython -I -B product/scoped-fixture/build.py --commit $Commit --output $NewOutput`。构建器仅从 Git 对象读取插件白名单、部署说明和入口的 Core Python 导入闭包，统一 ZIP 时间戳。交付的外部 inventory 列明源码提交、ZIP 与安装清单摘要。安装清单校验安装包全部文件，检查发生在服务启动及工具调用，用户本机运行环境和第三方 SDK 属于本地信任边界。
