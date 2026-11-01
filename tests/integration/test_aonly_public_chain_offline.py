"""Supervisor routing over original AF records, ONLY synthetic custody/TEST_ONLY Grant.

No Supervisor constructor, socket, native process, real issuer, or Solver. The
trusted fixture Grant replaces issuance; this does not qualify protected IPC/HIL.
"""

import copy
import importlib
import json
import sys
from types import SimpleNamespace

import pytest

from aegiscae.contracts.research_contracts import ContractError
from aegiscae.research.rod_real_verify import verify_owner_artifact_set
from test_d4_cross_repo_offline import joined as _joined_fixture

joined = _joined_fixture


class OnePass:
    def __init__(self):
        self.calls = 0

    def wait(self, _timeout):
        self.calls += 1
        return self.calls > 1


@pytest.fixture
def routed(joined, monkeypatch):
    _research, af, helper, _binding, _port = joined
    # Avoid cached helpers holding classes from a prior isolated AF import set.
    sys.modules.pop("test_d6_rod_authority", None)
    d6 = importlib.import_module("test_d6_rod_authority")
    from abqjobpilot.execution import standard_contract as standard
    from abqjobpilot.execution.managed_process import ManagedScope
    from abqjobpilot.execution.supervisor import FakeSupervisor

    def forbidden(*_args, **_kwargs):
        raise AssertionError("NATIVE_OR_REAL_AUTHORITY_FORBIDDEN")

    monkeypatch.setattr(FakeSupervisor, "__init__", forbidden)
    monkeypatch.setattr(ManagedScope, "create_standard", forbidden)
    monkeypatch.setattr(standard, "_issue", forbidden)
    d6.synthetic_protected(af, monkeypatch)
    shell = object.__new__(FakeSupervisor)
    shell.context, shell.store, shell.service = af.context, af.store, af.service
    shell.last_error, shell.lifecycle, shell._stop = None, None, OnePass()
    try:
        yield SimpleNamespace(af=af, helper=helper, d6=d6, shell=shell, launches=[])
    finally:
        sys.modules.pop("test_d6_rod_authority", None)


def control(case, request):
    return case.shell._invoke("product_standard_control", {"request": request})


def authorize_test_only(case, monkeypatch):
    from abqjobpilot.execution import standard_contract as standard
    from abqjobpilot.execution.models import ExecutionPlan, require
    from execution_helpers import FakeGrantFixture

    control(case, case.d6.request(case.af))
    decision = case.d6.decision_record(case.af)
    # Controlled fixture data preparation, outside the public management transaction.
    grant_id = FakeGrantFixture(case.af.store).issue_exact(ExecutionPlan.from_dict(case.af.plan))

    def existing_fixture(service, conn, plan, expiry, _source):
        assert service is case.af.service and plan["plan_digest"] == case.af.plan["plan_digest"]
        grant = json.loads(conn.execute("SELECT body FROM grants WHERE grant_id=?", (grant_id,)).fetchone()[0])
        assert grant["grant_kind"] == "TEST_ONLY" and "approval_operation" not in grant
        grant["expires_at"] = expiry
        return grant

    def strict_test_grant(_service, plan, grant, consumed, run_id):
        require(grant["grant_kind"] == "TEST_ONLY" and grant["issuer"] == "FakeGrantFixture"
                and grant["plan_id"] == plan["plan_id"] and grant["plan_digest"] == plan["plan_digest"]
                and (consumed is None or consumed == run_id), "GRANT_SCOPE_MISMATCH", "TEST_ONLY exact fixture")

    monkeypatch.setattr(standard, "_issue", existing_fixture)
    monkeypatch.setattr(standard, "check_grant", strict_test_grant)
    request = case.d6.authorization(case.af, decision)
    result = control(case, request)
    assert result["receipt"]["grant_id"] == grant_id
    assert control(case, request)["replayed"]
    return grant_id


def submit_arm(case, monkeypatch, *, lose_reply=False):
    from abqjobpilot.execution.models import now

    grant_id = authorize_test_only(case, monkeypatch)
    request = case.helper.request(case.af, grant_id)
    if lose_reply:
        def lost(stage):
            if stage == "submit:before_response":
                raise RuntimeError("SYNTHETIC_LOST_REPLY")
        monkeypatch.setattr(case.shell, "_checkpoint", lost)
        with pytest.raises(RuntimeError, match="SYNTHETIC_LOST_REPLY"):
            case.shell._invoke("submit", {"request": request})
        monkeypatch.setattr(case.shell, "_checkpoint", lambda _stage: None)
    accepted = case.shell._invoke("submit", {"request": request})
    run_id = accepted["receipt"]["run_id"]
    run = case.shell._invoke("run", {"run_id": run_id})
    dispatch = case.d6.request(case.af, "dispatch_once", key="route_dispatch", arguments={
        "run_id": run_id, "revision": run["revision"], "gate_version": case.af.store.gate()["version"],
        "start_not_after": now() + 20})
    control(case, dispatch)
    assert control(case, dispatch)["replayed"]

    def runner(*args, **kwargs):
        case.launches.append(run_id)
        return case.helper.synthetic_runner(*args, **kwargs)
    monkeypatch.setattr(case.af.service._standard_backend, "execute", runner)
    return run_id


def public_artifacts(case, monkeypatch):
    from abqjobpilot import product_rod
    product = object.__new__(product_rod.RodProduct)
    product.directory, product.context = case.af.context.runtime_root, case.af.context
    monkeypatch.setattr(product_rod, "ServiceLifecycleManager", lambda _directory: SimpleNamespace(
        _profile=lambda: {"client_namespace": case.af.service.client_namespace}))
    return product.read_real_artifacts(case.af.plan["plan_id"], case.af.plan["plan_digest"], "request_a")


@pytest.mark.parametrize("lose_reply", [False, True])
def test_supervisor_routing_test_only_once_and_public_three_artifacts(joined, routed, monkeypatch, lose_reply):
    research, _af, _helper, binding, _port = joined
    run_id = submit_arm(routed, monkeypatch, lose_reply=lose_reply)
    routed.shell._work()
    assert routed.shell.last_error is None
    assert routed.shell._invoke("receipt", {"idempotency_key": "request_a"})["run_id"] == run_id
    assert routed.shell._invoke("validations", {"run_id": run_id})
    from abqjobpilot.execution.supervisor import MAX_EVENTS
    assert routed.shell._invoke("events", {"after_sequence": 0, "limit": MAX_EVENTS})
    routed.shell._stop = OnePass()
    routed.shell._work()
    assert routed.launches == [run_id]
    value = public_artifacts(routed, monkeypatch)
    result = verify_owner_artifact_set(value, research.inspect()["candidates"]["A"], binding)
    assert result["numerical_bytes_check"] == "PASS"
    assert result["V2"] == "NOT_VERIFIED" and result["V3"] == "INCONCLUSIVE"
    assert len(value["artifacts"]) == 3
    with routed.af.store.read() as conn:
        assert all(conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] == 1
                   for t in ("runs", "grants", "consumption", "receipts"))


@pytest.mark.parametrize("damage", ["owner", "token", "scope", "denial"])
def test_supervisor_public_review_rejects_before_fixture_grant(routed, damage):
    value = routed.d6.request(routed.af)
    if damage == "owner":
        value["owner_id"] = "wrong_owner"
    elif damage == "token":
        value["operator_token"] = "ordinary_agent"
    elif damage == "scope":
        value["arguments"]["scope_digest"] = "wrong_scope"
    else:
        value["arguments"]["decision"] = "DENY_TERMINAL"
        control(routed, value)
        value = routed.d6.authorization(routed.af, routed.d6.decision_record(routed.af))
    with pytest.raises(routed.helper.ExecutionError):
        control(routed, value)
    with routed.af.store.read() as conn:
        assert all(conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] == 0
                   for t in ("runs", "grants", "receipts"))


@pytest.mark.parametrize("extension", ["dat", "sta", "msg"])
def test_public_reader_rejects_changed_original_file(routed, monkeypatch, extension):
    submit_arm(routed, monkeypatch)
    routed.shell._work()
    (routed.af.engineering / (routed.af.plan["job_name"] + "." + extension)).write_bytes(b"polluted")
    with pytest.raises(routed.helper.ExecutionError):
        public_artifacts(routed, monkeypatch)


def test_transport_change_rejected_by_independent_three_artifact_reader(joined, routed, monkeypatch):
    research, _af, _helper, binding, _port = joined
    submit_arm(routed, monkeypatch)
    routed.shell._work()
    envelope = copy.deepcopy(public_artifacts(routed, monkeypatch))
    envelope["artifacts"][1]["run_id"] = "another_run"
    with pytest.raises(ContractError):
        verify_owner_artifact_set(envelope, research.inspect()["candidates"]["A"], binding)


def test_worker_failure_retains_unknown_slot_and_never_reexecutes(routed, monkeypatch):
    run_id = submit_arm(routed, monkeypatch)
    def failed(*_args, **_kwargs):
        routed.launches.append(run_id)
        raise RuntimeError("SYNTHETIC_EXECUTION_RESPONSE_UNKNOWN")
    monkeypatch.setattr(routed.af.service._standard_backend, "execute", failed)
    routed.shell._work()
    assert routed.shell.last_error is not None
    assert routed.af.store.gate()["state"] == "PAUSED"
    routed.shell._stop = OnePass()
    routed.shell._work()
    assert routed.launches == [run_id]
    with routed.af.store.read() as conn:
        assert conn.execute("SELECT run_id FROM slot WHERE id=1").fetchone()[0] == run_id
