# Tensile usability profile source

Maintained source overlay for GD `0.1.0-tensile.10` / AF
`0.0.0+tensileusability1`. This directory is source, not an installed plugin or a
research workspace. No credentials, native project databases, ODB files or live
operation journals are included.

`SOURCE_MANIFEST.json` records both repository commits and the pre-existing AF
dirty paths, the exact `.9` frozen baseline source hashes, and every changed
file. `overlay/` is the maintained source of those changes; `SOURCE_DIFF.patch`
is their exact review diff. The existing AF working tree was not overwritten.
The original release remains unchanged. No automatic Git commit is performed.

Rebuild using the existing approved interpreter, exact frozen baseline artifact,
and a new independent destination:

```powershell
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -I -B -S '.\rebuild.py' --baseline '<exact-.9-freeze-directory>' --destination '<new-independent-directory>' --build
```

The recipe verifies baseline bytes and overlay hashes before reconstructing
source, creates a canonical wheel/ZIP, and installs with pip `--target` only in
the new candidate. It does not install into a shared environment, create a
research Plan, start Owner or call Solver. Absolute installation paths are part
of the runtime qualification; a rebuild at a different path intentionally has
a different site-bound identity and requires its own acceptance.

Tests distinguish substituted scientific/ODB data, actual native Windows IPC,
and TEST_ONLY button automation. See the candidate's developer report and
independent Testing report before any installation/onsite use. The original
cross-boot B lifecycle is not qualified for a new execution window by this work.

See [local trust scope](../../docs/architecture/LOCAL_TENSILE_EXECUTION_TRUST.md)
and the external audit disposition. References/HMAC are not human signatures;
the native Grant remains the execution authority after the exact local decision.
