"""Synthetic contract evidence only: no installed AF, owner, Project or solver."""

import builtins
import importlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, replace
from types import SimpleNamespace
from types import ModuleType

import pytest

from aegiscae.adapters.abaqus.af_evidence import EvidenceBridge
from aegiscae.contracts.af_evidence import ProjectBinding, ReadCursor, SourceIdentity


def ident(prefix, number=1):
    return f"{prefix}_{number:032x}"


BINDING = ProjectBinding(r"Q:\synthetic\instance", ident("p"), ident("pi"),
                         "sha256:" + "a" * 64, ident("owner"))
RUN = ident("r")
SECRET = "INJECTED_SECRET_DO_NOT_DISCLOSE"
READS = ["health", "project_view", "run", "receipt", "events", "validations", "diagnose"]


def run_record(number=1):
    return {"run_id": ident("r", number), "project_id": BINDING.project_id,
            "project_instance_id": BINDING.project_instance_id, "revision": 1,
            "created_at": 100, "queue_state": "DISPATCHED", "execution": "FINISHED",
            "solver_conclusion": "NOT_RUN", "artifact_validation": "VALID",
            "reconciliation": "NONE", "backend_id": "fake-v1", "simulation": True,
            "validation_scope": "simulation", "plan_id": ident("plan", number),
            "plan_digest": "sha256:" + "c" * 64}


def validation(number=1):
    return {"validation_id": ident("val", number), "run_id": RUN,
            "verdict": "PASS", "scope": "simulation", "recorded_at": 100,
            "policy_id": "fake-result-v1", "policy_version": 1,
            "validator_id": "fake-json-validator", "validator_version": 1}


def event(number, run_number=1, kind="REQUEST_ACCEPTED"):
    return {"event_id": ident("ev", number), "run_id": ident("r", run_number),
            "project_sequence": number, "type": kind, "recorded_at": 100}


class UpstreamError(Exception):
    def __init__(self, code, stage="QUERY"):
        super().__init__(SECRET + r" Q:\private\credential.json")
        self.code, self.stage = code, stage
        self.token = SECRET


class TransportDouble:
    def __init__(self):
        self.endpoint = {"protocol": "af-local-json-v1", "project_id": BINDING.project_id,
                         "project_instance_id": BINDING.project_instance_id,
                         "context_digest": BINDING.context_digest, "owner_id": BINDING.owner_id}
        self.health_data = {"operations": READS + ["submit", "validate_run", "lifecycle_stop"],
                            "simulation": True}
        self.calls = []
        self.runs = [run_record(number) for number in range(70, 0, -1)]
        self.events_data = [event(number, 1 if number % 2 else 2) for number in range(1, 71)]
        self.run_data = run_record()
        self.receipt_data = {"request_id": ident("req"), "run_id": RUN,
                             "namespace": json.dumps([BINDING.project_instance_id,
                                                      "synthetic-private", "submit"]),
                             "idempotency_key": "original-key", "request_status": "ACCEPTED",
                             "accepted_at": 100}
        self.validations_data = [validation()]
        self.diagnostic_data = {
            "content_digest": "sha256:" + "b" * 64,
            "body": {"report_version": "af-run-diagnostic-v1",
                     "identity": {**self.endpoint, "run_id": RUN},
                     "view": {"read_at": 100, "all_run_records_within_limits": True},
                     "facts": {"run": run_record(), "validations": [validation()]}}}
        self.error = None

    def _record(self, name, *args):
        self.calls.append((name, *args))
        if self.error:
            raise self.error

    def project_view(self, before_row=0, limit=32):
        self._record("project_view", before_row, limit)
        rows = [item for item in self.runs
                if before_row == 0 or int(item["run_id"][2:], 16) < before_row]
        next_row = int(rows[limit - 1]["run_id"][2:], 16) if len(rows) > limit else None
        return {**self.endpoint, "view_version": "af-project-view-v1", "runs": rows[:limit],
                "next_before_row": next_row, "read_at": 100 + len(self.calls)}

    def run(self, run_id):
        self._record("run", run_id)
        return self.run_data

    def receipt(self, key):
        self._record("receipt", key)
        return self.receipt_data

    def events(self, after_sequence=0, limit=64):
        self._record("events", after_sequence, limit)
        return [item for item in self.events_data if item["project_sequence"] > after_sequence][:limit]

    def validations(self, run_id):
        self._record("validations", run_id)
        return self.validations_data

    def diagnose(self, run_id):
        self._record("diagnose", run_id)
        return self.diagnostic_data

    def __getattr__(self, name):
        raise AssertionError("Unexpected transport surface: " + name)


@pytest.fixture
def bridge():
    client = TransportDouble()
    context = SimpleNamespace(project_id=BINDING.project_id,
                              project_instance_id=BINDING.project_instance_id,
                              context_digest=BINDING.context_digest)
    discoveries = []

    def discover(root):
        discoveries.append(root)
        return client, context, client.health_data

    return EvidenceBridge(discover), client, context, discoveries


def invoke_all(facade):
    return [facade.capabilities(BINDING), facade.list_runs(BINDING),
            facade.get_run(BINDING, RUN), facade.get_receipt(BINDING, "original-key"),
            facade.list_events(BINDING), facade.get_validations(BINDING, RUN),
            facade.get_diagnostic(BINDING, RUN)]


def test_seven_reads_only_and_reauthenticate_each_call(bridge):
    facade, client, _, discoveries = bridge
    results = invoke_all(facade)
    assert all(item.error is None and item.completeness == "COMPLETE" for item in results)
    assert all(item.source.owner_id == BINDING.owner_id for item in results)
    assert len(discoveries) == 7 and set(discoveries) == {BINDING.root}
    assert {call[0] for call in client.calls} == set(READS) - {"health"}
    assert results[0].data["execution_authorized"] is False
    assert set(results[0].data["read_operations"]) == {
        "capabilities", "list_runs", "get_run", "get_receipt", "list_events",
        "get_validations", "get_diagnostic"}
    assert results[-1].data["digest_verified"] is False
    assert not hasattr(facade, "client")
    for name in ("call", "submit", "validate_run", "export_diagnostic", "start_service"):
        with pytest.raises(AttributeError):
            getattr(facade, name)


@pytest.mark.parametrize("target,field,value", [
    ("context", "project_id", ident("p", 2)),
    ("context", "project_instance_id", ident("pi", 2)),
    ("context", "context_digest", "sha256:" + "f" * 64),
    ("endpoint", "project_id", ident("p", 2)),
    ("endpoint", "project_instance_id", ident("pi", 2)),
    ("endpoint", "context_digest", "sha256:" + "f" * 64),
    ("endpoint", "owner_id", ident("owner", 2)),
    ("endpoint", "protocol", "unknown"),
])
def test_identity_mismatch_no_query_or_fallback(bridge, target, field, value):
    facade, client, context, discoveries = bridge
    if target == "context":
        setattr(context, field, value)
    else:
        client.endpoint[field] = value
    result = facade.get_run(BINDING, RUN)
    assert result.error.code in {"PROJECT_IDENTITY_MISMATCH", "ENDPOINT_IDENTITY_MISMATCH",
                                 "PROTOCOL_MISMATCH"}
    assert result.source is None and result.data is None
    assert client.calls == [] and len(discoveries) == 1


@pytest.mark.parametrize("code", ["LEGACY_PROJECT", "OWNER_NOT_RUNNING", "DISCOVERY_UNAVAILABLE",
                                 "LOCAL_CREDENTIAL_UNAVAILABLE", "UNSUPPORTED_FORMAT"])
def test_discovery_failure_is_typed_single_attempt(code):
    calls = []

    def discover(root):
        calls.append(root)
        raise UpstreamError(code, "DISCOVERY")

    result = EvidenceBridge(discover).get_run(BINDING, RUN)
    assert result.error.code == code and result.error.stage == "DISCOVERY"
    assert result.completeness == "UNAVAILABLE" and len(calls) == 1
    assert SECRET not in repr(result)


@pytest.mark.parametrize("root", ["", ".", "relative", r"Q:relative", r"\\server\share",
                                 r"Q:\safe\..\unsafe", r"\\?\Q:\device"])
def test_invalid_root_never_discovers(bridge, root):
    facade, _, _, discoveries = bridge
    assert facade.capabilities(replace(BINDING, root=root)).error.code == "INVALID_BINDING"
    assert discoveries == []


def test_import_constructor_failure_have_no_process_or_write_effects(monkeypatch):
    effects = []

    def forbidden(*args, **kwargs):
        effects.append("forbidden")
        raise AssertionError("side effect")

    original_import = builtins.__import__
    original_open = builtins.open

    def readonly_open(file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in "wax+"):
            return forbidden()
        return original_open(file, mode, *args, **kwargs)

    def isolated_import(name, *args, **kwargs):
        if name.startswith("abqjobpilot"):
            return forbidden()
        return original_import(name, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "__import__", isolated_import)
        patch.setattr(builtins, "open", readonly_open)
        patch.setattr(subprocess, "Popen", forbidden)
        patch.setattr(os, "system", forbidden)
        patch.setattr(os, "mkdir", forbidden)
        module = importlib.reload(sys.modules["aegiscae.adapters.abaqus.af_evidence"])
        module.EvidenceBridge()
        facade = module.EvidenceBridge(lambda root: (_ for _ in ()).throw(OSError(SECRET)))
        result = facade.get_run(BINDING, RUN)
        assert result.error.code == "UPSTREAM_UNAVAILABLE"
    assert effects == []


def test_real_lazy_seam_with_synthetic_module_only(monkeypatch, bridge):
    _, client, context, _ = bridge
    calls = []
    package = ModuleType("abqjobpilot")
    module = ModuleType("abqjobpilot.service_discovery")

    def synthetic_discover(root):
        calls.append(root)
        return client, context, client.health_data

    module.discover = synthetic_discover
    monkeypatch.setitem(sys.modules, "abqjobpilot", package)
    monkeypatch.setitem(sys.modules, "abqjobpilot.service_discovery", module)
    facade = EvidenceBridge()
    assert calls == []
    assert facade.capabilities(BINDING).error is None
    assert calls == [BINDING.root]


@pytest.mark.parametrize("shape", ["deep", "wide", "aggregate_bytes", "cycle"])
def test_response_tree_budgets_fail_closed(bridge, shape):
    facade, client, _, _ = bridge
    if shape == "deep":
        value = None
        for _ in range(13):
            value = {"nested": value}
    elif shape == "wide":
        value = [None] * 8193
    elif shape == "aggregate_bytes":
        value = ["x" * 131073] * 2
    else:
        value = []
        value.append(value)
    client.run_data["private"] = value
    result = facade.get_run(BINDING, RUN)
    assert result.error.code == "LIMIT_EXCEEDED" and result.data is None


@pytest.mark.parametrize("field", ["project_id", "project_instance_id"])
def test_run_response_must_retain_its_native_identity(bridge, field):
    facade, client, _, _ = bridge
    del client.run_data[field]
    assert facade.get_run(BINDING, RUN).error.code == "PROJECT_IDENTITY_MISMATCH"


def test_bad_receipt_namespace_is_typed_and_safe(bridge):
    facade, client, _, _ = bridge
    client.receipt_data["namespace"] = SECRET
    result = facade.get_receipt(BINDING, "original-key")
    assert result.error.code == "MALFORMED_RESPONSE" and SECRET not in repr(result)


def test_70_runs_keyset_pagination(bridge):
    facade, client, _, discoveries = bridge
    pages, ids, cursor = [], [], None
    while True:
        page = facade.list_runs(BINDING, cursor)
        assert page.error is None
        pages.append(page)
        ids.extend(item["run_id"] for item in page.data)
        cursor = page.next_cursor
        if cursor is None:
            break
    assert [len(page.data) for page in pages] == [32, 32, 6]
    assert len(ids) == len(set(ids)) == 70
    assert [call[1] for call in client.calls] == [0, 39, 7]
    assert len({page.source_read_at for page in pages}) == 3
    assert all("not_atomic" in page.consistency for page in pages)
    assert len(discoveries) == 3


def test_interleaved_event_filter_and_raw_high_watermark(bridge):
    facade, _, _, _ = bridge
    first = facade.list_events(BINDING, limit=64, run_id=RUN)
    second = facade.list_events(BINDING, cursor=first.next_cursor, run_id=RUN)
    assert len(first.data) == 32 and len(second.data) == 3
    assert first.next_cursor.position == 64 and second.next_cursor.position == 70
    assert first.more_possible is True and second.more_possible is False
    assert all(item["run_id"] == RUN for item in first.data + second.data)


@pytest.mark.parametrize("unknown", [False, True])
def test_filtered_empty_page_advances_without_false_terminal(bridge, unknown):
    facade, client, _, _ = bridge
    client.events_data = [event(i, 2, "FUTURE_KIND" if unknown else "REQUEST_ACCEPTED")
                          for i in range(1, 65)] + [event(65)]
    first = facade.list_events(BINDING, run_id=RUN)
    assert first.data == () and first.next_cursor.position == 64 and first.more_possible is True
    assert first.completeness == ("INCOMPLETE" if unknown else "COMPLETE")
    second = facade.list_events(BINDING, first.next_cursor, run_id=RUN)
    assert len(second.data) == 1 and second.next_cursor.position == 65


def test_cursor_cannot_cross_owner_or_operation(bridge):
    facade, client, _, _ = bridge
    cursor = facade.list_runs(BINDING).next_cursor
    for bad in [replace(cursor, operation="list_events"),
                replace(cursor, source=replace(cursor.source, owner_id=ident("owner", 2))),
                replace(cursor, position=True), replace(cursor, position=-1)]:
        client.calls.clear()
        result = facade.list_runs(BINDING, bad)
        assert result.error.code == "INVALID_CURSOR" and client.calls == []


@pytest.mark.parametrize("raw,code", [
    ([validation(i) for i in range(65)], "LIMIT_EXCEEDED"),
    ({"records": [validation()]}, "MALFORMED_RESPONSE"),
    ([{"validation_id": "bad", "run_id": RUN}], "MALFORMED_RESPONSE"),
    ([{**validation(), "run_id": ident("r", 2)}], "PROJECT_IDENTITY_MISMATCH"),
    ([{**validation(), "secret": "x" * 262145}], "LIMIT_EXCEEDED"),
])
def test_unpaged_validations_never_truncate_to_success(bridge, raw, code):
    facade, client, _, _ = bridge
    client.validations_data = raw
    result = facade.get_validations(BINDING, RUN)
    assert result.error.code == code and result.completeness == "UNAVAILABLE"
    assert result.data is None


def test_unknown_missing_status_never_becomes_pass(bridge):
    facade, client, _, _ = bridge
    client.run_data["execution"] = SECRET
    del client.run_data["artifact_validation"]
    result = facade.get_run(BINDING, RUN)
    assert result.completeness == "INCOMPLETE"
    assert result.data["execution"] is None and result.data["artifact_validation"] is None
    client.validations_data[0]["verdict"] = SECRET
    result = facade.get_validations(BINDING, RUN)
    assert result.completeness == "INCOMPLETE" and result.data[0]["recorded_verdict"] is None


def test_all_nested_secret_paths_and_grants_are_excluded(bridge):
    facade, client, _, _ = bridge
    injection = {"token": SECRET, "Grant": {"operator_token": SECRET},
                 "path": "Q:/private/" + SECRET, "credential": SECRET}
    for raw in [client.health_data, client.run_data, client.receipt_data,
                *client.runs, *client.events_data, *client.validations_data,
                client.diagnostic_data, client.diagnostic_data["body"],
                client.diagnostic_data["body"]["facts"]["run"],
                *client.diagnostic_data["body"]["facts"]["validations"]]:
        raw["private"] = injection
    results = invoke_all(facade)
    assert all(result.error is None for result in results)
    encoded = json.dumps([asdict(result) for result in results])
    assert SECRET not in encoded and "synthetic-private" not in encoded
    assert "original-key" not in encoded and "Grant" not in encoded
    assert BINDING.root not in repr(BINDING)


@pytest.mark.parametrize("code", ["NOT_FOUND", "COMMUNICATION_UNKNOWN", SECRET])
def test_receipt_uncertainty_no_resubmission_or_key_replacement(bridge, code):
    facade, client, _, discoveries = bridge
    client.error = UpstreamError(code, SECRET)
    result = facade.get_receipt(BINDING, "original-key")
    assert result.error.code == (code if code != SECRET else "UPSTREAM_UNAVAILABLE")
    assert result.error.stage == "QUERY" and result.data is None
    assert client.calls == [("receipt", "original-key")] and len(discoveries) == 1
    assert SECRET not in repr(result)


def test_no_capability_means_no_query(bridge):
    facade, client, _, _ = bridge
    client.health_data["operations"] = ["health", "submit"]
    assert facade.get_run(BINDING, RUN).error.code == "CAPABILITY_UNAVAILABLE"
    assert client.calls == []


@pytest.mark.parametrize("operation", ["list_runs", "list_events"])
@pytest.mark.parametrize("limit", [0, True, 65])
def test_invalid_page_limits_no_query(bridge, operation, limit):
    facade, client, _, _ = bridge
    assert getattr(facade, operation)(BINDING, limit=limit).error.code == "INVALID_REQUEST"
    assert client.calls == []


def test_malformed_event_sequence_and_diagnostic_identity(bridge):
    facade, client, _, _ = bridge
    client.events_data = [event(2), event(1)]
    assert facade.list_events(BINDING).error.code == "MALFORMED_RESPONSE"
    client.diagnostic_data["body"]["identity"]["project_id"] = ident("p", 2)
    assert facade.get_diagnostic(BINDING, RUN).error.code == "PROJECT_IDENTITY_MISMATCH"


def test_owner_changes_between_calls_are_not_cached(bridge):
    facade, client, _, discoveries = bridge
    assert facade.get_run(BINDING, RUN).error is None
    client.endpoint["owner_id"] = ident("owner", 2)
    assert facade.get_run(BINDING, RUN).error.code == "ENDPOINT_IDENTITY_MISMATCH"
    assert len(discoveries) == 2 and len(client.calls) == 1


def test_missing_run_cursor_is_not_a_terminal_success(bridge, monkeypatch):
    facade, client, _, _ = bridge
    original = client.project_view

    def malformed(**kwargs):
        result = original(**kwargs)
        del result["next_before_row"]
        return result

    monkeypatch.setattr(client, "project_view", malformed)
    result = facade.list_runs(BINDING)
    assert result.error.code == "MALFORMED_RESPONSE"
    assert result.data is None and result.more_possible is None


@pytest.mark.parametrize("solver", ["NOT_RUN", "EVIDENCE_INSUFFICIENT",
                                   "COMPLETED_TEXT_EVIDENCE", "FAILED_TEXT_EVIDENCE"])
def test_recorded_standard_solver_states_keep_exact_scope(bridge, solver):
    facade, client, _, _ = bridge
    client.run_data.update(backend_id="abaqus-standard-axial-2024-v1", simulation=False,
                           validation_scope="fixed_standard_dat_only", solver_conclusion=solver)
    result = facade.get_run(BINDING, RUN)
    assert result.error is None and result.data["solver_conclusion"] == solver
    assert result.data["simulation"] is False
    assert result.data["validation_scope"] == "fixed_standard_dat_only"


def test_missing_optional_provenance_is_unknown_not_inferred(bridge):
    facade, client, _, _ = bridge
    for field in ("simulation", "validation_scope", "plan_digest"):
        del client.run_data[field]
    result = facade.get_run(BINDING, RUN)
    assert result.data["backend_id"] == "fake-v1"
    assert result.data["simulation"] is None and result.data["validation_scope"] is None
    assert result.data["plan_digest"] is None
    del client.run_data["backend_id"]
    assert facade.get_run(BINDING, RUN).completeness == "INCOMPLETE"


def test_source_identity_does_not_include_root():
    identity = SourceIdentity(BINDING.project_id, BINDING.project_instance_id,
                              BINDING.context_digest, BINDING.owner_id)
    assert set(asdict(identity)) == {"project_id", "project_instance_id", "context_digest", "owner_id"}
    assert ReadCursor(identity, "list_events", 1).position == 1
