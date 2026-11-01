"""External-only installed-package smoke; no AF service imports or solver APIs."""

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys


def smoke(destination):
    import aegiscae

    root = Path(aegiscae.__file__).parent / "_gdcae_plugin"
    spec = spec_from_file_location("gdcae_installed_setup", root / "scripts/gdcae.py")
    setup = module_from_spec(spec)
    spec.loader.exec_module(setup)
    setup.installed_package("aegiscae", "aegiscae")
    setup.installed_package("abqjobpilot", "abqjobpilot_gdcae_internal")
    setup.installed_plugin_copy()
    digest = setup.content_digest(setup.read_package())
    workspace = destination / "project"
    initialized = setup.initialize_research(workspace, digest, "ExternalOfflineSmoke")
    if initialized["real_a"] != "NOT_RUN" or initialized["execution_authorized"]:
        raise ValueError("UNEXPECTED_AUTHORITY")
    doctor = setup.doctor(workspace)
    if doctor["workspace"]["status"] != "PACKAGE_AND_FOUR_ROLE_BYTES_VERIFIED":
        raise ValueError("CLOSURE_FAILED")
    real = setup.initialize_real_research(destination / "real-contract-project",
                                          digest, "ExternalRealContractSmoke")
    if real["plan_created"] or real["grant_issued"] or real["execution_authorized"]:
        raise ValueError("UNEXPECTED_AUTHORITY")
    if real["real_a"] != "NOT_READY" or real["real_b"] != "NOT_RUN":
        raise ValueError("UNEXPECTED_REAL_CLAIM")
    # Genuine persisted projects were initialized; no research execution ran.
    result = dict.fromkeys(("install", "import_record", "plugin_resources", "doctor",
                            "init", "offline_project_smoke", "real_contract_freeze",
                            "no_execution_authority"), "PASS")
    with (destination / "smoke.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True)


if __name__ == "__main__":
    try:
        smoke(Path(sys.argv[1]))
    except Exception:
        # No exception/path/evidence echo outside the independent disposable VM.
        raise SystemExit(2) from None
