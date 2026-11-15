# 一次性迁移到固定 Commit 的 Git Marketplace

适用于 Windows 上已经经由官方 Git Marketplace 安装的 GD-CAE Research Preview。请等发布者提供通过审阅的目标 Tag、完整 Commit、Manifest 和 ZIP SHA-256，以及已上线的 Pre-release。更新组件使用 Windows PowerShell、Git 和 Codex CLI；科研 Core 的 Python 环境独立管理。

## 先确定电脑上实际有什么

关闭使用该配置的 Codex 窗口和后台会话，在普通 PowerShell 中读取磁盘快照。这个阶段不要启动会刷新旧分支的 Codex 会话。保留此前的验收记录。以下命令不需要管理员权限。

```powershell
$ErrorActionPreference = 'Stop'
$homePath = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$market = 'gdcae-research-preview'
$name = 'gdcae-research'
$url = 'https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator.git'
$snap = Join-Path $homePath ".tmp\marketplaces\$market"
$oldCommit = git -C $snap rev-parse HEAD
if ($LASTEXITCODE -or $oldCommit -cnotmatch '^[0-9a-f]{40}$') { throw '请核对实际的 Codex 配置目录与市场来源' }
$origin = git -C $snap remote get-url origin
if ($LASTEXITCODE -or $origin -cne $url) { throw '来源与官方 Git 市场不一致' }
$trees = @(Get-ChildItem -LiteralPath (Join-Path $homePath "plugins\cache\$market\$name") -Directory)
if ($trees.Count -ne 1) { throw '安装身份存在歧义，保留现状并报告' }
$oldVersion = (Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $trees[0].FullName 'plugin.json') | ConvertFrom-Json).version
$oldManifest = (Get-FileHash -LiteralPath (Join-Path $trees[0].FullName 'package-manifest.json')).Hash.ToLowerInvariant()
[pscustomobject]@{Version=$oldVersion; Commit=$oldCommit; Manifest=$oldManifest}
```

将这三项与该实际版本的官方 Tag、Release 和清单比对。如果已超过目标版本、来源不同、出现多个同名启用项或任一摘要不符，停止迁移。保留已有项目、Runtime、模型、输出及验收记录。

另行记录该配置实际登记的市场引用和启用状态。仅将已经存在的 Host 回执或配置中的对应市场项用于这一步。目录存在不能证明 enabled；快照 HEAD 是本地已下载的提交，注册的 ref 仍可能是分支。记录字段为来源、市场名、插件 ID、版本、注册 ref、快照 HEAD、enabled 和 Manifest。无法确认的字段记 UNKNOWN。不要把包含其他账户或连接器信息的完整配置贴进验收记录。

### 遇到移动分支，先选安全的迁移路径

- 已登记完整 Commit 且来源、快照、已启用安装和 Tag 一致，可以保留该实例，按后文取得入口并展示更新要约。
- 仍登记分支时，Host 在启动时可能自行刷新。在能够保留当前基线的既有 Host 中，可使用后文的 `pin-current` 固定 **实际观察到的** 版本。若存在启动即换版的风险，请保持旧配置关闭。不要为测试是否会更新而重启它。
- 若用户同意在独立 Codex 配置中继续 UAT，可在下述步骤中直接从已批准的目标 Commit 建立新的固定安装。旧配置保留为历史证据。这个操作属于**一次性迁移安装**。若 B 必须使用原 Desktop 配置且没有经过验证的安全切换入口，请保留原配置并记录迁移阻断。

独立配置的操作仅在固定 Tag 和 Pre-release 通过远端验收后执行。先向用户展示正式发行记录中的目标、Commit、两个摘要、安装位置及旧配置的处置，得到确认。使用 B 机实际支持的 Codex CLI，在单独 PowerShell 窗口中执行，保持该窗口的配置作用域：

```powershell
$ErrorActionPreference = 'Stop'
$newHome = Join-Path $env:LOCALAPPDATA 'GDCAE-UAT\codex-fixed-preview'
if (Test-Path -LiteralPath $newHome) { throw '目标已存在，先核实此前安装，避免重复' }
$env:CODEX_HOME = (New-Item -ItemType Directory -Path $newHome).FullName
# 使用已批准发行表填写 $newCommit、$newVersion、$newManifest。窗口中重新设置 $url 与 $market。
$url = 'https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator.git'
$market = 'gdcae-research-preview'
if ($newCommit -cnotmatch '^[0-9a-f]{40}$' -or $newManifest -cnotmatch '^[0-9a-f]{64}$') { throw '缺少固定发行身份' }
$added = codex plugin marketplace add $url --ref $newCommit --sparse .agents/plugins --sparse plugins/gdcae-research --json | ConvertFrom-Json
if ($LASTEXITCODE -or $added.marketplaceName -cne $market) { throw '固定市场登记失败' }
$head = git -C $added.installedRoot rev-parse HEAD
if ($LASTEXITCODE -or $head -cne $newCommit) { throw '暂存 HEAD 不符' }
$pkg = Join-Path $added.installedRoot 'plugins\gdcae-research'
$mf = Join-Path $pkg 'package-manifest.json'
if ((Get-FileHash -LiteralPath $mf).Hash -ne $newManifest) { throw 'Manifest 不符' }
$entry = Join-Path $pkg 'scripts\update.ps1'
$m = Get-Content -LiteralPath $mf -Raw -Encoding UTF8 | ConvertFrom-Json
if ($m.version -cne $newVersion -or (Get-FileHash -LiteralPath $entry).Hash -ne $m.files.'scripts/update.ps1') { throw '入口身份不符' }
$expected = @('package-manifest.json') + @($m.files.PSObject.Properties.Name)
$tree = @(Get-ChildItem -LiteralPath $pkg -Force -Recurse)
if (@($tree | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw '文件树含重解析点' }
$actual = @($tree | Where-Object { !$_.PSIsContainer } | ForEach-Object { $_.FullName.Substring($pkg.Length+1).Replace('\','/') })
if (Compare-Object -CaseSensitive $expected $actual) { throw '暂存文件集合不符' }
foreach ($f in $m.files.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Join-Path $pkg $f.Name)).Hash -ne $f.Value) { throw '暂存文件摘要不符' }
}
codex plugin add "gdcae-research@$market" --json
if ($LASTEXITCODE) { throw '安装失败，保留回执' }
powershell.exe -NoProfile -File $entry -Action verify -TargetVersion $newVersion -TargetCommit $newCommit -ManifestPin $newManifest
if ($LASTEXITCODE) { throw '安装文件或持久引用核验失败' }
```

在同一新配置内按需通过官方界面登录；打开新会话，检查 research 与 setup 的来源、版本、enabled 和首次 Skill 的实际回执。日后应通过能明确选中该固定配置的入口进入；普通桌面快捷方式可能仍使用旧配置。只有此配置内的完整验收才计入迁移结果。无需搬运 ZIP 或复制认证文件。科研项目和 Runtime 继续保存在原来的外部位置；需要使用 Core 时按新版本重新绑定。

## 从固定提交取得原配置的迁移入口

在同一窗口中，将发行批准表中的**目标**版本和摘要赋给 `$newVersion`、`$newCommit`、`$newManifest`、`$newZip`。从 [官方 Preview 发行页](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases)核对这四项。下列命令仅登记单独的暂存市场，原配置在 finally 中恢复。

```powershell
if ($newCommit -cnotmatch '^[0-9a-f]{40}$' -or $newManifest -cnotmatch '^[0-9a-f]{64}$' -or $newZip -cnotmatch '^[0-9a-f]{64}$') { throw '请填写发行批准表' }
$savedHome = $env:CODEX_HOME
$stage = Join-Path $env:TEMP ('gdcae-pin-migration-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $stage | Out-Null
try {
    $env:CODEX_HOME = $stage
    $added = codex plugin marketplace add $url --ref $newCommit --sparse .agents/plugins --sparse plugins/gdcae-research --json | ConvertFrom-Json
    if ($LASTEXITCODE -or $added.marketplaceName -cne $market) { throw '暂存市场失败' }
    $stagedCommit = git -C $added.installedRoot rev-parse HEAD
    if ($LASTEXITCODE -or $stagedCommit -cne $newCommit) { throw '暂存提交不符' }
    $pkg = Join-Path $added.installedRoot "plugins\$name"
    $manifest = Join-Path $pkg 'package-manifest.json'
    if ((Get-FileHash -LiteralPath $manifest).Hash -ne $newManifest) { throw '清单不符' }
    $m = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifest | ConvertFrom-Json
    $entry = Join-Path $pkg 'scripts\update.ps1'
    if ($m.version -cne $newVersion -or (Get-FileHash -LiteralPath $entry).Hash -ne $m.files.'scripts/update.ps1') { throw '升级入口不符' }
} finally { $env:CODEX_HOME = $savedHome }
```

## 确认两项不同的变更

以下是修订后入口的 Host 命令。普通 PowerShell 只用于前面的只读盘点和隔离暂存。固定旧版本时，由同一 Codex 对话的授权 GitHub 连接器读取当前版本的官方 Tag 和 Release，再由 Host 调用 pin-current。若启动该 Host 可能抢先刷新仍跟踪分支的旧安装，先停止迁移并保留盘点结果。进入固定版本后的更新测试不覆盖这个初次迁移场景。

1. 展示第一步的实际版本与 Commit。用户确认**固定当前版本**后，执行下列第一条命令。它读取官方 Tag 与 Release，核验旧包，使用 Codex 官方配置接口将当前分支引用固定到同一 Commit，并核验 enabled 与实际文件。收到 `PINNED_CURRENT` 后保留回执。若已经是目标版本，直接进入新会话核验。
2. 如果目标 Tag 已发布、官方频道尚未推进，可以先完成固定旧版本。请维护者在旧分支用户固定当前版本后再推进频道。仅在官方频道 HEAD 和目标 Tag 同时指向上述目标 Commit 时，按插件 references/update.md 在同一 Host 对话收集发行回执，执行 -Action offer 并展示两个版本、两个 Commit、变更、重启影响及两个目标摘要；确认用户选择**立即更新**后，才执行第二条命令。暂不更新就继续使用已固定的原版本。每条命令单独执行、检查退出码，在第一项失败时停下。

```powershell
# 用户确认固定当前版本后
powershell.exe -NoProfile -File $entry -Action pin-current -TargetVersion $oldVersion -TargetCommit $oldCommit -ManifestPin $oldManifest -ConfirmUpdate
if ($LASTEXITCODE) { throw '固定旧版本未通过，请保留现场' }
```

```powershell
# 仅在用户另行确认更新要约后
powershell.exe -NoProfile -File $entry -Action install -FromCommit $oldCommit -TargetVersion $newVersion -TargetCommit $newCommit -ManifestPin $newManifest -ZipPin $newZip -ConfirmUpdate
if ($LASTEXITCODE) { throw '保留回执与旧安装，不自动重试' }
```

打开新 Codex 会话，确认唯一启用的官方插件、两个 Skill 的实际来源和版本，用新版安装入口执行 `-Action verify`，传入上述目标版本、Commit、Manifest。以后从 setup/research 首次调用即可检查版本并在对话中选择更新，无需搬运 ZIP。若 Host 拒绝网络或写权限，此次更新会停止；保留固定旧版并继续科研。
