# CAE Agent 0.3.1

`service/` 提供标准本地 stdio MCP。`market/` 提供可选的 Codex 适配器 `cae-agent@cae-agent-local`。二者有独立清单，外部交付回执记录源码提交和 SHA-256。研究合同由操作人员显式提供，服务读取数据、检查资格和判据，客户端根据工具回执提出候选。当前可运行的测试适配器和参考合同位于 `examples/cae_agent/`，使用前须明确选择 TEST_ONLY Fixture。真实 Abaqus 调用预算为 0。

## 本地部署

从独立交付回执取得 ZIP 和两份清单的摘要，校验 ZIP 后解压到新目录。以下 PowerShell 变量表示部署人员选定的绝对路径和摘要。A 机运行时为 Windows CPython 3.12.10 / MCP SDK 2.3.0；协议 QA 用 psutil 7.2.2 检查子进程退出。在登记的解释器环境中先核对：

```powershell
& $Python -I -B -c "import sys,mcp,win32api,psutil,importlib.metadata as v; print(sys.executable,sys.version,v.version('mcp'),psutil.__version__)"
$Service = Join-Path $Unpacked 'service'
$Setup = Join-Path $Unpacked 'configure.py'
```

### 标准客户端

操作人员选择新研究根目录、独立绑定文件、作用域、资源、上限和有效期。三个目标文件/目录使用新路径，父目录需已存在。可独立配置 Core 并从任意支持 stdio 的 MCP 客户端连接，示例如下。

```powershell
& $Python -I -B $Setup --service-root $Service --service-sha256 $ServiceManifestSha --profile $Profile --binding $ScopeFile --new-project $ProjectRoot --contract-file $ExplicitContract --max-executions $ApprovedLimit --ttl-seconds $LifetimeSeconds
& $Python -I -B (Join-Path $Service 'serve.py') gdcae-core --profile $Profile
```

标准客户端使用上例最后一行的可执行文件与参数，通过 stdin/stdout 协商协议。可重跑的独立客户端检查为 `& $Python -I -B (Join-Path $Unpacked 'qa/neutral_check.py') --profile $Profile --output $NewReceipt`。它调用项目打开、诊断和状态，返回工具名、修订和状态摘要。授权已有项目时使用原绑定及独立授权回执 `--binding-sha256 $OriginalScopePin` 替换新建参数。更改版本、绑定、预算或合同须按新的作用域重新核验。

新建作用域时可重复传入 `--allow-operation <工具名>` 明确缩小授权集合。省略该参数时使用该版本的十项固定操作；绑定回执列出实际授权操作。

### Codex 适配器及 Classic

独立 A 机验收使用全新临时 Host 配置目录。不要复制账户文件。将本地 Marketplace 加到要实际测试的客户端配置，安装插件，然后在单次绑定时同时指定适配器和可选 Classic。示例使用以前已核对的本机隔离 Classic 工程及一条惰性队列记录。

```powershell
$env:CODEX_HOME = $IsolatedHostHome
& $DesktopCodex plugin marketplace add (Join-Path $Unpacked 'market')
& $DesktopCodex plugin add 'cae-agent@cae-agent-local'
$Adapter = Join-Path $IsolatedHostHome 'plugins/cache/cae-agent-local/cae-agent/0.3.1'
$Profile = Join-Path $IsolatedHostHome 'cae-agent/deployment.json'
& $Python -I -B $Setup --service-root $Service --service-sha256 $ServiceManifestSha --profile $Profile --adapter-root $Adapter --adapter-sha256 $AdapterManifestSha --provider $ReviewedClassicZip --classic-root $IsolatedClassicProject --classic-id $ExpectedClassicUUID --backend-work-root $PermittedInertWorkRoot --queue-id $InertQueueID --binding $ScopeFile --new-project $ProjectRoot --contract-file $ExplicitContract --max-executions $ApprovedLimit --ttl-seconds $LifetimeSeconds
```

Classic 使用独立部署的 0.2.2 官方源码归档，提交 `7012133e7cc0176bb3e56fc24d7154ee3b90bb81`，SHA-256 `34bb598048e24dbbe180ea1255227383012f1858579c2f8468cead1ac994d5df`。可复用原有 T02 部署或从已核对的上游源码用仓库 `product/research-preview/tools/prepare_abq_service.py` 的 `service_archive` 导出。新机可选择专用新目录并用 `--create-empty-classic` 替代 UUID 和队列标识参数，调用官方 ProjectManager 创建空工程。该模式只读取队列和历史。若未部署 Classic，可以在首次绑定时省略整组 Classic 参数单用 Core。资料、源码与授权文件均留在用户本机。

## 普通 Desktop 自然语言验收

1. 使用实际启用本适配器及已绑定合同的 Desktop 配置进入普通聊天。发送“请在已授权的项目中，根据实际研究目标和工具回执完成一次候选迭代，报告证据、判定与停止原因”。保留该真实对话的工具事件。
2. 核对模型主动调用项目、任务、诊断、状态工具，并从合同读取目标、变量和可用操作。记录模型在看到首次结果前给出的候选、理由和工具请求。
3. 在测试专用范围内可要求“先用一个越界候选检验拒绝，再在原范围内修正”。核对拒绝回执和预算，再保留模型自行修正的合法候选。第一次未满足目标时，检查 `gdcae_evidence_read` 返回摘要、模型给出的新候选及其引用。测试人员无需逐步回复“继续”。
4. 记录终态、重开时的项目、修订、候选与证据。分别记录协议调用、模型生成的提案和自然路由。只有普通 Desktop 实际选择工具的观测可填写该项 PASS。

## 可重跑的安装态协议检查

`qa/installed_check.py` 使用 Desktop 随附 app-server、独立 Host 配置与新进程。首次调用读取双服务、绑定合同与实际修订；每次运行保存一份新回执。选定测试合同须显式使用 `examples/cae_agent/contract.json`。首轮工具调用和每次复开如下。

```powershell
$Check = Join-Path $Unpacked 'qa/installed_check.py'
$Market = Join-Path $Unpacked 'market'
& $Python -I -B $Check --codex $DesktopCodex --home $IsolatedHostHome --market $Market --classic-check --output $FirstReceipt
& $Python -I -B $Check --codex $DesktopCodex --home $IsolatedHostHome --market $Market --proposal-file $CallerProposal --output $NextReceipt
```

输入 JSON 包含 `expected_revision`、稳定 `key` 和完整 `proposal`（变量、值、单位、基线摘要、理由和证据引用），来自执行当时的客户端。拒绝会保存实际错误及原修订；接受后只推进该候选。下一个候选由调用者看到证据后另行提交。回执不确定时可用 `--query-key $OriginalKey` 核对原请求。结束时省略 `--proposal-file` 重新打开并比对状态摘要。预设协议测试使用 `examples/cae_agent/test-proposals.json`，明确为 SCRIPTED_PROTOCOL_TEST_DATA。

源码构建命令为 `& $Python -I -B product/cae-agent/build.py --commit $FullCommit --output $NewDirectory`。构建器使用 Git 白名单、入口的静态导入闭包和固定 ZIP 时间戳。安装和每次产生副作用前检查文件内容、项目身份、绑定和有效期。此部署依赖受信的本地 OS 用户、解释器和所选依赖环境。
