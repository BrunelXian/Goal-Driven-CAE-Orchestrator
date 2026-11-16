# AbqJobPilot 只读工程服务

在已核实的 Research Main 中打开 T02。Main 根据任务提出检查，显示将查询的后端项目和队列范围，以及写入科研账本的证据。用户同意后，由 Main 查询并读回 T02。用户可继续进行科研讨论，或推迟这次检查。

## 供部署人员使用

当前支持 Windows x64、已绑定的 CPython 3.12.10、MCP SDK 2.3.0（含 Windows pywin32 依赖）、AbqJobPilot 0.2.2 正式 stdio 服务。仅有标准库的 Managed Runtime 可继续支持原科研功能；使用 T02 需要部署具备这些依赖、通过绑定核验的解释器。插件不会安装依赖。

1. 从受信的部署记录取得当前 Desktop Host、Desktop Project、后端 Project 的独立 UUID 及本地根目录，选用经审核的上游源仓库。安装包中的 `runtime/abq-readonly.json` 记录支持的提交和服务源码归档摘要。
2. 在开发/部署环境（本仓库 `src` 可导入）运行下列命令。使用已核实的解释器绝对路径。部署只导出固定提交中的供应方 Python 文件，不读取工程模型，不采纳研究任务提供的命令。重复部署接受字节完全相同的记录，已有冲突时停止。

```powershell
& $VerifiedPython product/research-preview/tools/prepare_abq_service.py --repository $ReviewedCheckout --host $HostId --desktop $DesktopProject --backend-root $BackendRoot --backend-id $BackendUuid
```

3. 每个 Desktop Project 具有单独的本地服务配置。ResearchProject 和 T02 还需对该配置、后端 UUID 与队列选择分别绑定。只读证据保存在该部署目录下的 `observations/<项目身份摘要>/<证据摘要>.json`；任务账本只引用文件名及 SHA-256。保留这两处数据供恢复。部署目录位于用户 LocalAppData，依靠操作系统用户和已审查的依赖环境作为本地信任边界。
4. 调用顺序为 `task-list → t02-plan → 用户同意 → task-update → t02-read → task-list`。未登记授权时返回 `T02_READ_CONSENT_REQUIRED`。后端身份不符返回 `BACKEND_PROJECT_MISMATCH`。缺少服务配置、SDK 或握手失败均保留具体失败状态。对 SDK 和服务可用性以真实连接结果为准。
5. 返回的队列和历史各至多 50 条，仅留存数量、来源和响应摘要。选定作业返回状态及标识摘要。此观测只证明服务当时的回复，`SUBMITTED` 表示 T02 证据已提交。科学判定和作业执行权分别由原有门禁管理。

本地验收入口为 `tests/integration/installed_t02_checks.py`。传入通过 Marketplace 安装的候选、独立 Manifest 摘要、固定上游仓库及新的外部工作目录。该测试使用合成 Main 回执与真实 stdio；真实 Desktop Main 的回执另行核对。
