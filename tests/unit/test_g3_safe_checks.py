"""Synthetic identity checks; no real commit, credential or thread data."""

from copy import deepcopy

import pytest

from g3_safe_checks import AF_PARENT, GD_PARENT, checkpoint_identity
from m03f1_safe_replay import ProjectionBlocked


def receipt():
    return {"schema": "g3-checkpoint-receipt-v1", "status": "CROSS_REPO_CHECKPOINT_PARTIAL",
            "push": False, "real_abaqus": False,
            "gdcae": {"status": "PASS_LOCAL_OFFLINE_CHECKPOINT", "commit_count": 1,
                       "parent": GD_PARENT, "head": "a" * 40},
            "af": {"status": "BLOCKED_LINT", "commit_count": 0, "head": AF_PARENT}}


def test_checkpoint_maps_actual_partial_authority_without_global_head_patch():
    import g1_safe_checks
    import m03f1_safe_replay
    before = g1_safe_checks.HEAD, m03f1_safe_replay.HEAD
    assert checkpoint_identity(receipt()) == ("a" * 40, AF_PARENT)
    assert (g1_safe_checks.HEAD, m03f1_safe_replay.HEAD) == before


@pytest.mark.parametrize("scope,key,value", [
    (None, "schema", "other"), (None, "status", "PASS_REAL"),
    (None, "push", True), (None, "real_abaqus", True),
    ("gdcae", "head", "main"), ("gdcae", "head", GD_PARENT),
    ("gdcae", "parent", "b" * 40), ("gdcae", "commit_count", True),
    ("gdcae", "commit_count", 2), ("gdcae", "status", "PASS_REAL"),
    ("af", "head", "c" * 40), ("af", "commit_count", 1),
    ("af", "status", "PASS"),
])
def test_unreviewed_checkpoint_identity_is_rejected(scope, key, value):
    record = deepcopy(receipt())
    target = record if scope is None else record[scope]
    target[key] = value
    with pytest.raises(ProjectionBlocked):
        checkpoint_identity(record)
