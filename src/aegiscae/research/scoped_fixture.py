"""Compatibility entry points for the versioned TEST_ONLY automated spring regression."""
from aegiscae.research import scoped_coordinator


def start(project, scope_id, max_runs, expected_revision, key):
    return scoped_coordinator.start(project, scope_id, max_runs, expected_revision, key)


def advance(project, scope_id, max_runs, expected_revision, key, proposal=None):
    return scoped_coordinator.advance(project, scope_id, max_runs, expected_revision, key, proposal)


def status(project, scope_id, max_runs, request_key=None):
    return scoped_coordinator.status(project, scope_id, max_runs, request_key)
