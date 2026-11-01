"""Real public AF preflight method over original synthetic fixture records.

The fixture supplies the facade's read-only service factory and StandardConfig;
this is not protected Product deployment, human consent or real execution.
GD production code only consumes the public projection, never an AF Store.
"""

import copy

import pytest

from aegiscae.contracts.research_contracts import ContractError
from aegiscae.research import rod_real_project as real
from test_d4_cross_repo_offline import joined as _joined_fixture

joined = _joined_fixture


class PublicPreflight:
    def __init__(self, af, monkeypatch):
        from abqjobpilot.product_rod import RodProduct

        # Trusted fixture-only reader factory substitution, no production DB access
        # by GD and no actual protected lifecycle/profile provisioning is claimed.
        self.product = object.__new__(RodProduct)
        self.product.context = af.context
        monkeypatch.setattr(self.product, "_reader", lambda: af.service)
        self.config = af.config
        self.calls = 0

    def preflight_real(self, **kwargs):
        self.calls += 1
        return self.product.preflight_real(config=self.config, **kwargs)


def assert_no_af_execution(af):
    # Assertions below inspect only the isolated trusted test fixture.
    with af.store.read() as conn:
        assert all(conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] == 0
                   for table in ("runs", "grants", "receipts", "consumption"))


def test_actual_public_preflight_creates_one_persistent_gd_application(joined, monkeypatch):
    research, af, _helper, binding, _port = joined
    port = PublicPreflight(af, monkeypatch)
    result = research.hold_a_for_review(port, binding, 3, "d6_hold_A")
    assert port.calls == 1 and result["budget"]["held"] == 1
    assert result["project_revision"] == 4
    snapshot = result["form"]["preflight"]
    assert snapshot["plan_digest"] == af.plan["plan_digest"]
    assert snapshot["research_contract"]["contract_digest"] == research.inspect()["contract_digest"]
    assert snapshot["real_a_output"] == "NOT_PRODUCED"
    assert result["form"]["status"] == "NOT_EXECUTABLE"
    assert not result["execution_authorized"]
    assert research.a_only_application()["application_digest"] == result["application_digest"]
    assert_no_af_execution(af)


def test_unknown_replay_does_not_requery_or_regenerate_exact_request(joined, monkeypatch):
    research, af, _helper, binding, _port = joined
    port = PublicPreflight(af, monkeypatch)
    first = research.hold_a_for_review(port, binding, 3, "d6_hold_A")
    research.record_intent_a(4, "d6_intent_A")
    research.mark_unknown_a(5, "d6_unknown_A")
    def no_query(**_kwargs):
        pytest.fail("committed UNKNOWN replay must not refresh remote evidence")
    monkeypatch.setattr(port, "preflight_real", no_query)
    replay = research.hold_a_for_review(port, binding, 3, "d6_hold_A")
    assert replay["application_digest"] == first["application_digest"]
    assert replay["query_first_required"] and replay["reservation_state"] == "ACCEPTANCE_UNKNOWN"
    with pytest.raises(ContractError, match="REAL_ATTEMPT_ALREADY_RESERVED"):
        research.hold_a_for_review(port, binding, 6, "d6_new_key")
    assert replay["budget"] == {"limit": 2, "held": 1, "charged": 0, "available": 1}
    assert_no_af_execution(af)


def test_lost_local_commit_response_replays_original_public_snapshot(joined, monkeypatch):
    research, af, _helper, binding, _port = joined
    port = PublicPreflight(af, monkeypatch)
    def fault(stage):
        if stage == "after_commit":
            raise RuntimeError("D6_SYNTHETIC_LOST_REPLY")
    monkeypatch.setattr(real, "_fault", fault)
    with pytest.raises(RuntimeError, match="D6_SYNTHETIC_LOST_REPLY"):
        research.hold_a_for_review(port, binding, 3, "d6_hold_A")
    monkeypatch.setattr(real, "_fault", lambda _stage: None)
    monkeypatch.setattr(port, "preflight_real", lambda **_kwargs: pytest.fail("new read forbidden"))
    result = research.hold_a_for_review(port, binding, 3, "d6_hold_A")
    assert result["replayed"] and result["budget"]["held"] == 1
    assert result["form"]["preflight"]["plan_id"] == af.plan["plan_id"]
    assert_no_af_execution(af)


@pytest.mark.parametrize("damage", ["project", "resources", "nonce", "approval", "output"])
def test_public_projection_corruption_cannot_reserve(joined, monkeypatch, damage):
    research, af, _helper, binding, _port = joined
    actual = PublicPreflight(af, monkeypatch)
    class CorruptPort:
        def preflight_real(self, **kwargs):
            value = copy.deepcopy(actual.preflight_real(**kwargs))
            if damage == "project":
                value["project_instance_id"] = "foreign_instance"
            elif damage == "resources":
                value["resources"]["cpus"] = 2
            elif damage == "nonce":
                value["research_contract"]["request_nonce"] = "new_nonce"
            elif damage == "approval":
                value["execution_authorized"] = True
            else:
                value["declared_outputs"][0]["path"] = "C:/Foreign/old.dat"
            return value
    before = research.inspect()
    with pytest.raises(ContractError):
        research.hold_a_for_review(CorruptPort(), binding, 3, "d6_corrupt")
    assert research.inspect() == before
    assert_no_af_execution(af)
