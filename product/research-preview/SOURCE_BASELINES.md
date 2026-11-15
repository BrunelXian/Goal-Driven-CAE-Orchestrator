# Research Preview development source

The source history on main covers the verified Windows build inputs for the .12 and .13 prereleases and the cumulative .14/.15 personal-plugin work. The Git Marketplace channel and release tags have their own histories. A commit on main does not change either distribution.

| Preview | Standalone PUBLIC_DIRECTORY ZIP SHA-256 | package-manifest.json SHA-256 | Scope |
|---|---|---|---|
| .12 | fae0f74a87f49aed32687b89c826f693cac2c1c5ffbcbc837d1e806a738f4d2c | a16453b47796cfaa36b23736fece138efe526279fd72b72ce448a7444333a35b | Reconstructed from frozen source inputs. Release tag points to f7a872a70cb4705d7cfbb0f3d01c58d15a6e8cf3. Package validation was partial. |
| .13 | c8cd8b86475be5cf6c6e06b117b2d8301ce9de7bc4492e4fac2c4c00eba7972f | 5d72a88a74ed68db59c9f04d46bc674936f0a401e2b4b7de3e3779f9a1355277 | Reconstructed from frozen source inputs. Release tag points to 61d2f5db1b61a522ed6e90bbb2db50f4ee755dcf. Package and prior A-side update mechanism qualified; no claim of release-specific E2E. |
| .14 | 015d91bcfcb1d2429b2d7136a07252272fd94273aca46ad160c26417dbcc2ec8 | b71e519d044796961d72dd011e24dd100f24ccb277d117d22a512c7cfea66a7f | Private Creator normalization fix, retained in .15. The saved .14 artifact was checked; a distinct development commit with the original .14 packager is not asserted. |
| .15 | b643901c57d3492278ea0f53d163b1769358b20d3120621005266390a4ad79fe | bb5ab3914a36130c28e08d39feb31bfc69473ff6f854c558fc24af0ae133f4cf | Private Creator baseline. One maintained onboarding definition is rendered into both packaged Skills. |

## Rebuild the private .15 identity

Use a clean checkout, Windows x64 CPython 3.12.10 and the existing release tool. Obtain the original .15 root plugin.json from the approved private package. Keep this file outside the repository. The public development manifest omits the personal publisher email. The packager checks the external file's exact SHA-256 and all remaining metadata against the public source before using the approved bytes. A missing or different file stops the build. This is a build-time input only; the installed plugin, runtime verifier and package members retain their reviewed identities.

PowerShell, from the repository root, using paths chosen on the build machine:

~~~powershell
$env:GDCAE_PREVIEW15_PUBLISHER_MANIFEST = (Resolve-Path -LiteralPath $PrivateManifest).Path
& $PythonExe -I -B product/research-preview/tools/release.py --public-zip $FreshZipOutsideCheckout
~~~

Use a fresh external destination. Compare both returned hashes with the .15 row. For .12 or .13 check out the corresponding development snapshot and use its own release.py; these two public builds do not need the private publisher input. Core Python source is tracked; generated Core ZIPs, Python binaries and user bindings are not build inputs in Git.

The Git update boundary tests use the original Git Marketplace file layout. The Creator regression separately tests the platform-generated compatibility metadata and refuses modified metadata, executable files and unexpected members.
