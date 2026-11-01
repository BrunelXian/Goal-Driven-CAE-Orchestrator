"""Original AF transaction/collector records, fake authority and no native runner.

AF's trusted fixture prepares its own isolated store through its test framework.
GD production code only sees the public read port and never imports an AF Store.
"""

import importlib
import os
from pathlib import Path
import sys

import pytest

from aegiscae.contracts.research_contracts import ContractError, digest_bytes
from aegiscae.research.rod_evidence import af_digest
from aegiscae.research.rod_real_project import create_real_research


@pytest.fixture
def joined(tmp_path, monkeypatch):
    source = os.environ.get("GDCAE_G2_AF_SOURCE")
    if not source:
        pytest.skip("Explicit AF Develop required; no live source selected")
    root = Path(source)
    assert root.is_absolute() and (root / "tests/test_d4_rod_trusted.py").is_file()
    before = set(sys.modules)
    monkeypatch.syspath_prepend(str(root))
    monkeypatch.syspath_prepend(str(root / "tests"))
    helper = importlib.import_module("test_d4_rod_trusted")
    research = create_real_research(tmp_path / "research", "D4 cross repository synthetic chain")
    view = research.inspect()
    candidate = view["candidates"]["A"]
    fixture_root = tmp_path / "af-fixture"
    fixture_root.mkdir()
    fixture = helper.make_case(fixture_root, monkeypatch, {
        "research_project_id": view["research_project_id"], "contract_digest": view["contract_digest"],
        "research_revision": view["project_revision"], "candidate_id": candidate["candidate_id"],
        "request_nonce": "exact_nonce_a"})
    af = next(fixture)
    binding = {"project_id": af.context.project_id, "project_instance_id": af.context.project_instance_id,
        "plan_id": af.plan["plan_id"], "plan_digest": af.plan["plan_digest"],
        "input_digest": candidate["input_digest"], "resources_digest": af_digest(af.plan["resources"]),
        "output_identity": af.plan["output_key"], "candidate_output_identity": candidate["output_identity"],
        "request_key": "request_a", "request_nonce": "exact_nonce_a", "backend_id": af.plan["backend_id"]}
    class ReadPort:
        def read_real_artifact(self, **kwargs):
            return af.service.read_rod_artifact(af.context, **kwargs)
    try:
        yield research, af, helper, binding, ReadPort()
    finally:
        fixture.close()
        for name in tuple(set(sys.modules) - before):
            if name == "abqjobpilot" or name.startswith("abqjobpilot.") or name == "test_d4_rod_trusted":
                del sys.modules[name]


def complete(joined, monkeypatch):
    research, af, helper, binding, port = joined
    research.reserve_a(binding, 3, "reserve_A")
    research.record_intent_a(4, "intent_A")
    run_id = helper.complete_fixture(af, monkeypatch)
    return run_id, port


def test_actual_original_af_records_independent_gd_read_and_persistent_unknown(joined, monkeypatch):
    research, _af, _helper, binding, _port = joined
    run_id, port = complete(joined, monkeypatch)
    state = research.observe_a(port, 5, "observe_A")
    observation = state["observations"]["A"]
    assert observation["independent"]["run_id"] == run_id
    assert observation["independent"]["numerical_bytes_check"] == "PASS"
    assert observation["independent"]["V2"] == "NOT_VERIFIED"
    assert observation["evidence"]["run"]["phase"] == "STANDARD_ANALYSIS"
    assert observation["evidence"]["run"]["revision"] > 3
    assert observation["independent"]["plan_digest"] == binding["plan_digest"]
    assert state["budget"]["held"] == 1 and state["budget"]["charged"] == 0
    with pytest.raises(ContractError, match="AUTHENTICATED_REAL_A_REQUIRED"):
        research.propose_b({"native_role": "gdcae-inverse", "load_n": "2"}, 6, "forged_B")
    assert research.inspect() == {k: v for k, v in state.items() if k != "replayed"}


def test_original_dat_pollution_stops_public_read_and_preserves_gd_revision(joined, monkeypatch):
    research, af, helper, _binding, _port = joined
    _run_id, port = complete(joined, monkeypatch)
    before = research.inspect()
    (af.engineering / (af.plan["job_name"] + ".dat")).write_bytes(b"new untrusted bytes")
    with pytest.raises(helper.ExecutionError):
        research.observe_a(port, 5, "bad_source")
    assert research.inspect() == before


def test_schema_pass_and_recomputed_hash_do_not_bypass_independent_numbers(joined, monkeypatch):
    research, _af, _helper, _binding, _port = joined
    _run_id, port = complete(joined, monkeypatch)
    class CorruptTransport:
        def read_real_artifact(self, **kwargs):
            envelope = port.read_real_artifact(**kwargs)
            # Every artifact byte changes; the new checksum is not authentication.
            body = envelope["artifact"]["dat_bytes"] + b"\nTRAILING_UNTRUSTED_TABLE\n"
            envelope["artifact"].update(dat_bytes=body, size=len(body), sha256=digest_bytes(body))
            return envelope
    before = research.inspect()
    with pytest.raises(ContractError):
        research.observe_a(CorruptTransport(), 5, "bad_numeric")
    assert research.inspect() == before
