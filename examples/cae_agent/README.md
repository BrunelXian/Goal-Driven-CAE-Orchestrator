# 单次工具调用与可重现的协议回放

`call.py` 以标准 MCP SDK 初始化本地服务、读取工具表、提交由调用者提供的一项请求并输出结构化响应。它接受显式的工具名与 JSON 参数。创建项目的授权由独立的本机入口颁发。

以下 PowerShell 变量分别指向核实的 Python、源码根、隔离研究项目、绑定文件及其授权回执。绑定和研究项目使用新路径。安装态的受审服务启动命令见候选包的安装说明。

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
$receipt = & $VerifiedPython -B -m aegiscae.interfaces.research_scope --binding-file $Binding --project-root $Research --contract-file (Resolve-Path examples/cae_agent/contract.json).Path --max-executions 3 --ttl-seconds 3600 | ConvertFrom-Json
$env:GDCAE_BINDING_SHA256 = $receipt.binding_sha256
'{}' | & $VerifiedPython -B examples/cae_agent/call.py --source $env:PYTHONPATH --binding-file $Binding --tool gdcae_project_open
```

在仅打开过项目且还未启动工作流的测试作用域上回放：

```powershell
& $VerifiedPython -B examples/cae_agent/scenario.py --source $env:PYTHONPATH --binding-file $Binding --output $NewReport
```

`contract.json` 是该弹簧 Fixture 的合同样本。`test-proposals.json` 单独存放预选的协议测试输入。回放以 201 N 检查越界拒绝，随后提交 45 N，重开项目并用第一条证据的摘要提交 105 N。它从实际读回的原始观测、输入和合同重新计算判断与哈希。导出的报告标注 `SCRIPTED_PROTOCOL_TEST_DATA`、模型回合数和实际工具调用次数，并将本地项目标识替换为稳定标签。其他客户端可结合当前研究目标、任务与证据自行提出不同的候选。

提交结果不明确时用原 `project_id` 和 `request_key` 调用 `gdcae_workflow_status`，核对返回记录中的原候选、操作和预期修订。检查无法确认时保存状态并停止。
