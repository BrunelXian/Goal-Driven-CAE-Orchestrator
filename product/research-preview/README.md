# Research Preview 发行维护

插件的唯一维护源在 [plugins/gdcae-research](../../plugins/gdcae-research)。本目录持有本地 Marketplace 注册文件、安装指南模板、发行说明、已公开的历史小冲杆案例和标准库打包工具。运行环境为 Windows CPython 3.12.10。构建不需要配置 Codex、Abaqus 或外部小冲杆项目。

科研约定逻辑的维护源位于 [Core](../../src/aegiscae/research/research_agreement.py)。打包器按六项明确源码清单生成 `runtime/agreement-core.zip`，与插件清单一同校验。运行时从安装缓存加载，用户的版本记录仅写入自选项目的 `research.sqlite3`。四种 Markdown 视图、输入字段及迟到结果的归属见[科研约定操作说明](../../plugins/gdcae-research/references/research-agreement.md)。

从仓库根运行以下 PowerShell 命令。准备一个已核验的解释器和一个尚不存在的仓库外输出目录，父目录应已存在。

```powershell
$py = Read-Host 'Verified CPython 3.12.10 absolute path'
$out = Read-Host 'Fresh external output directory'
& $py -I -B -S product/research-preview/tools/release.py --build $out
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
$zip = (Get-ChildItem -LiteralPath $out -Filter '*.zip').FullName
& $py -I -B -S product/research-preview/tools/release.py --verify $zip
```

外层 ZIP 含发行 README、能力边界、公开指南与协议、历史案例、内层 ZIP 和 SHA256SUMS.txt。内层使用 `INSTALL-MEDIA` 根，注册后由宿主将插件复制到版本化缓存，操作者再显式绑定本机解释器。安装和复验命令见生成的安装指南。开发机路径、绑定回执、内部验收结果与完整科研项目仅保留在本地。

打包器逐项读取公开清单，核对历史案例和 SP 组件摘要，并从顶层 README 提取同一块十问十答。新增公开文件必须显式审查并加入清单。构建输出中的 inventory.json 给出内外层成员及包摘要。独立复验时从新目录重建，核对外层与内层摘要，再按安装指南执行 bind、doctor、历史项目正例和拒绝用例。检查桌面 Skill 调用时使用新身份 `gdcae-research:research`。

已安装后的开发复验入口如下。测试在显式传入的全新目录内创建独立绑定和故障样本。原历史项目只读。

```powershell
$cache = Read-Host 'Installed cache directory from plugin add'
$project = Read-Host 'Authorized historical SMALL-PUNCH root'
$test = Read-Host 'Fresh external test directory'
$pin = (Get-Content (Join-Path $out 'inventory.json') -Raw | ConvertFrom-Json).manifest_sha256
& $py -I -B -S product/research-preview/tools/verify_installed.py --installed $cache --manifest-pin $pin --project $project --output $test
```
