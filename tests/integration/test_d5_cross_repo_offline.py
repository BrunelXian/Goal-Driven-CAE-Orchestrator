"""D5 pre-A/readback seams on original AF records with synthetic execution only."""

import pytest

from test_d4_cross_repo_offline import complete, joined as _joined_fixture

joined = _joined_fixture


def test_frozen_gd_a_and_af_preflight_agree_without_future_outputs(joined):
    research, af, _helper, _binding, _port = joined
    from abqjobpilot.execution.rod_trusted import preflight

    before = research.inspect()
    draft = research.pre_a_dossier()
    expected = {k: v for k, v in af.arguments.items() if k != "expires_at"}
    expected["input_digest"] = before["candidates"]["A"]["input_digest"]
    result = preflight(af.service, af.context, plan_id=af.plan["plan_id"],
                       expected_plan_digest=af.plan["plan_digest"], expected_contract=expected)
    assert draft["status"] == "NOT_EXECUTABLE"
    assert draft["real_a_output"] == "NOT_AVAILABLE_TO_PROJECT"
    assert result["real_a_output"] == "NOT_PRODUCED"
    assert not result["execution_authorized"]
    assert draft["candidate_a"]["input_digest"] == expected["input_digest"]
    assert draft["budget_scope"] == "RESEARCH_PROJECT_ONLY"
    assert draft["campaign_budget_enforcement"] == "NOT_QUALIFIED"
    assert research.inspect() == before
    with af.store.read() as conn:
        assert all(conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] == 0
                   for table in ("runs", "grants", "receipts", "consumption"))


@pytest.mark.parametrize("extension", ["dat", "sta", "msg"])
def test_corrupt_original_completion_file_preserves_gd_unknown_budget(joined, monkeypatch,
                                                                     extension):
    research, af, helper, _binding, _port = joined
    _run_id, port = complete(joined, monkeypatch)
    before = research.inspect()
    (af.engineering / (af.plan["job_name"] + "." + extension)).write_bytes(b"D5_STALE_FIXTURE")
    with pytest.raises(helper.ExecutionError):
        research.observe_a(port, 5, "d5_corrupt_output")
    assert research.inspect() == before
    assert before["budget"]["held"] == 1 and before["budget"]["charged"] == 0


def test_fixture_completion_does_not_satisfy_real_goal_or_remove_authority_gates(joined,
                                                                              monkeypatch):
    research, _af, _helper, _binding, _port = joined
    _run_id, port = complete(joined, monkeypatch)
    state = research.observe_a(port, 5, "d5_observe")
    draft = research.pre_a_dossier()
    assert draft["status"] == "NOT_EXECUTABLE"
    assert draft["real_a_output"] == "UNAUTHENTICATED_RECORD_ONLY"
    assert draft["b_state"] == "NO_CANDIDATE_PLAN_OR_GRANT"
    assert draft["HIL_ENFORCEMENT"] == "BLOCKED"
    assert state["observations"]["A"]["independent"]["V2"] == "NOT_VERIFIED"
    assert state["observations"]["A"]["independent"]["V3"] == "INCONCLUSIVE"
