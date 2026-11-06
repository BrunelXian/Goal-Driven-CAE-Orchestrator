# GD-CAE Research Preview · Windows 本地安装

安装后，使用缓存中 `references/research-agreement.md` 的命令访问新建的科研约定项目。仅历史 SP 对比需要外部 SMALL-PUNCH 项目；科研约定操作需要用户自己的工程合同与新的显式项目目录。

版本 `0.2.0-preview.4`。本介质含本地 Marketplace、Main Skill、SP 历史分析组件和经摘要绑定的科研约定 Core 源码子集。请保留解压后的 INSTALL-MEDIA 目录，供宿主定位本地 Marketplace。

**先决条件**为支持本地 Marketplace 的 Codex 桌面客户端及其 CLI、PowerShell 和操作者已核验的 Windows CPython 3.12.10。分析仅需标准库。SP 历史比较另需具备读取权限的完整项目，包括 Sanity 和 run_014 公共 INP、CSV、来源、状态摘要及盲协议所指的访问策略元数据。外部 SP 项目只读，报告输出使用其外部的独立目录。

1. 将 ZIP 的 SHA256 与发布者独立提供的值核对。在本地持久目录解压。PowerShell 切换到其中的 INSTALL-MEDIA 目录，运行以下命令。在本机 CLI 支持 `plugin add` 时，安装结果会返回安装缓存目录。

```powershell
$medium = (Get-Location).Path
codex plugin marketplace add $medium --json
if ($LASTEXITCODE -ne 0) { throw 'Marketplace registration failed' }
$installed = codex plugin add gdcae-research@gdcae-research-agreements --json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or -not $installed.installedPath) { throw 'Inspect host installation result' }
$launcher = Join-Path $installed.installedPath 'scripts\launch.ps1'
```

2. 在本机选择一个已核验的解释器，输入其规范绝对路径。绑定前同时核对安装清单和 launcher 本身。这一步只在首次绑定时使用。记录输出的 `binding_sha256` 并与绑定文件分开保存。

```powershell
$manifestPin = '{{MANIFEST_SHA256}}'
$manifestFile = Join-Path $installed.installedPath 'package-manifest.json'
if ((Get-FileHash -LiteralPath $manifestFile -Algorithm SHA256).Hash -ne $manifestPin) { throw 'Package digest mismatch' }
$manifest = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $launcher -Algorithm SHA256).Hash -ne $manifest.files.'scripts/launch.ps1') { throw 'Launcher digest mismatch' }
$selectedPython = Read-Host 'Absolute path of your verified CPython 3.12.10 executable'
& $launcher -Action bind -PythonExe $selectedPython -ManifestSha256 $manifestPin
```

绑定文件位于本机用户 LocalAppData 下的 `GDCAE\gdcae-research\0.2.0-preview.4\binding.json`，含本机安装路径及运行文件指纹，应仅在本机保存。启动器每次先核对操作者保存的回执、解释器、基础可执行文件、已加载的 Python DLL 及适用的 venv 配置。Python 使用隔离模式、禁用 site 加载和字节码写入。已有绑定拒绝覆盖。若迁移安装或更新解释器，应由操作者保留旧回执及文件，再按新安装重新核验和绑定。

3. 用已保存的绑定 SHA256 运行 doctor。客户端提供 `gdcae-research:research` 后，在桌面选择该 Skill，提供绑定 SHA256、外部项目绝对路径和新输出目录。需要时重新打开客户端再检查技能目录。使用自然语言询问“run_014 的终点力接近历史 Sanity，能否接受新材料表，下一步最值得验证什么？”

```powershell
$receipt = Read-Host 'Saved binding SHA256'
& $launcher -Action doctor -BindingSha256 $receipt
```

可在本机直接复核安装入口，父目录须存在，输出目录须全新。

```powershell
$project = Read-Host 'Absolute path of your existing historical project'
$output = Read-Host 'Absolute path of a fresh external output directory'
& $launcher -Action main -BindingSha256 $receipt -ProjectRoot $project -OutputDirectory $output
```

成功后查看 `report.md`、`report.json` 和 `curve_difference.csv`。报告来自已有公共模型结果，可能含操作者的本机路径及项目来源标识，应在分享前另行审阅。材料物理验收需独立证据。此预览只执行历史数据对照。源码完整性、运行绑定、数据来源或访问策略检查失败时，应保留错误并停止。桌面 Skill 实际调用和独立验收另行记录。
