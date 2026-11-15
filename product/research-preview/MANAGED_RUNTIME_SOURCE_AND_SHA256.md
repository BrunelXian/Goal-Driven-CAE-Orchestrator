# CPython Runtime 来源和 SHA-256

发行对象为 Python Software Foundation 发布的 CPython 3.12.10 Windows x64 Embeddable Package，原始文件 python-3.12.10-embed-amd64.zip，11,133,606 字节；解压后 35 个文件共 22,501,299 字节。原包逐字节保留，未增删、重签或修改 ._pth。

官方发行页 https://www.python.org/downloads/release/python-31210/
原始下载 https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip
官方签名索引 https://www.python.org/downloads/metadata/pgp/
原始 SHA-256：4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3

A 端在独立 keyring 内验证 ZIP 的官方 OpenPGP 分离签名，得到 VALIDSIG，签名密钥指纹为 7ED10B6531D7C8E1BC296021FC624643487034E5，与 Python 官方发布的 Windows 签名者 Steve Dower 指纹一致。由已验证原始 ZIP 固定 SHA-256 及各成员身份。随附原始 .asc、Sigstore bundle 和 SPDX SBOM。实际采用 OpenPGP 验证。

GD-CAE 固定预发布镜像 https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/download/runtime-cpython-3.12.10-win-x64-r1/python-3.12.10-embed-amd64.zip
插件锁定版本、下载字节数、官方 SHA-256 和逐成员摘要。仅允许 GitHub 针对此仓库资产的一次 HTTPS 交付重定向。安装到用户 LocalAppData 的 GDCAE/runtimes 版本化目录。Windows x64 / UCRT；不安装 pip、Tk，不编辑系统 Python、注册表或 PATH。镜像 SHA-256 必须与官方原件一致。
