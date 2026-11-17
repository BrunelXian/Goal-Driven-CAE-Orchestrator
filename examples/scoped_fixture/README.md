# 有界位移 Fixture 回放

本例用经授权的 stdio 工具编排冻结的测试目标。Main 从测得的首个载荷和位移计算下一候选，Core 的独立判据重算 0.9–1.1 mm 区间并登记决定。

**安装态复现**使用发行包中的 `installed_case.py` 和安装指南。该入口让普通 Host 进程实际调用两个本地 MCP。此脚本的独立入口使用 MCP SDK stdio，可用于开发测试。

在已选择的本机解释器和新建的隔离目录中执行以下 PowerShell。研究项目和绑定文件都须使用新路径。路径变量由本机操作者指定。

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
$grant = & $VerifiedPython -B -m aegiscae.interfaces.fixture_scope --binding-file $BindingFile --project-root $FixtureProject --max-executions 3 --ttl-seconds 3600 | ConvertFrom-Json
$env:GDCAE_FIXTURE_BINDING_SHA256 = $grant.binding_sha256
& $VerifiedPython -B examples/scoped_fixture/rehearse.py --binding-file $BindingFile --output $NewReceiptFile
```

回放刻意在客户端丢弃首次已接受的计算回复。Main 重开服务，按原请求键查询项目、操作、预期修订、候选内容及摘要。缺少匹配的接收记录时停止。只读请求遇到存储占用或通信故障时至多重试两次，分别退避 0.05 和 0.15 秒。回执逐项标出尝试、延时及恢复原因。复核读回涵盖 CLAIMED 和终态两个时点的任务、项目修订、输入、预算、证据和下一步。

导出的 JSON 替换本机项目和存储身份，保留原始协议请求和响应的规范化 JSON SHA-256。所用弹簧、测点和方向都是测试定义。真实 Solver 预算为 0。
