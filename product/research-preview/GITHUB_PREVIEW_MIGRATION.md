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

## 从固定提交取得迁移入口

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

1. 展示第一步的实际版本与 Commit。用户确认**固定当前版本**后，执行下列第一条命令。它读取官方 Tag 与 Release，核验旧包，使用 Codex 官方配置接口将当前分支引用固定到同一 Commit，并核验 enabled 与实际文件。收到 `PINNED_CURRENT` 后保留回执。若已经是目标版本，直接进入新会话核验。
2. 如果目标 Tag 已发布、官方频道尚未推进，可以先完成固定旧版本。请维护者在旧分支用户固定当前版本后再推进频道。仅在官方频道 HEAD 和目标 Tag 同时指向上述目标 Commit 时，展示当前版本、目标版本、两个 Commit、变更、重启影响及两个目标摘要；确认用户选择**立即更新**后，才执行第二条命令。暂不更新就继续使用已固定的原版本。每条命令单独执行、检查退出码，在第一项失败时停下。

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
