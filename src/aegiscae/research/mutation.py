"""Synthetic-only staging and audited candidate publication; never an executor."""

import os
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from aegiscae.contracts.research_contracts import (
    ContractError, canonical_json, digest_bytes, identifier, require, strict_json,
)
from aegiscae.research import project as store
from aegiscae.research.mutation_rules import (
    MutationRequest, check_diff, edit_scalar, rejection, validate_parent, validate_record,
)


@dataclass(frozen=True)
class SyntheticWorkspace:
    _root: Path = field(repr=False)
    workspace_id: str


def _fault(stage):
    """Trusted synthetic fault injection only."""


def _test_root(explicit, *, exists=True):
    path = Path(explicit)
    require(path.is_absolute() and ".." not in path.parts
            and not any(part.casefold() == "cae models" for part in path.parts), "UNSAFE_TEST_ROOT")
    temporary = Path(tempfile.gettempdir()).resolve()
    require(path != temporary and path.is_relative_to(temporary), "TEMP_TEST_ROOT_REQUIRED")
    return store._path(path, exists=exists)


def _read_bytes(path):
    store._path(path, directory=False)
    before = path.stat()
    require(before.st_size <= 8192, "INPUT_LIMIT")
    with path.open("rb") as stream:
        body = stream.read(8193)
    store._path(path, directory=False)
    after = path.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            and len(body) == after.st_size, "CONCURRENT_FILE_CHANGE")
    return body


def _workspace_identity(root):
    return {"root_digest": digest_bytes(os.path.normcase(str(root.resolve())).encode()),
            "root_identity": store._file_id(root), "staging_identity": store._file_id(root / "staging")}


def _exclusive_file(path, body):
    """Only called after an owned, new staging directory or workspace was validated."""
    with path.open("xb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())


def create_synthetic_workspace(explicit_new_root):
    root = _test_root(explicit_new_root, exists=False)
    require(not root.exists(), "OUTPUT_EXISTS")
    root.mkdir()
    staging = root / "staging"
    staging.mkdir()
    workspace_id = "synthetic_" + uuid.uuid4().hex
    marker = {"schema_version": "synthetic-workspace-v1", "workspace_id": workspace_id,
              **_workspace_identity(root)}
    _exclusive_file(root / "synthetic.json", canonical_json(marker))
    return SyntheticWorkspace(root, workspace_id)


def _workspace(workspace):
    require(type(workspace) is SyntheticWorkspace, "INVALID_WORKSPACE")
    root = _test_root(workspace._root)
    store._path(root / "staging")
    raw = _read_bytes(root / "synthetic.json")
    marker = strict_json(raw)
    require(type(marker) is dict and set(marker) == {"schema_version", "workspace_id", "root_digest",
            "root_identity", "staging_identity"} and canonical_json(marker) == raw
            and marker["schema_version"] == "synthetic-workspace-v1"
            and marker["workspace_id"] == workspace.workspace_id
            and all(marker[key] == value for key, value in _workspace_identity(root).items()),
            "WORKSPACE_IDENTITY_MISMATCH")
    identifier(workspace.workspace_id, "synthetic")
    return root, digest_bytes(raw)


def _parent(meta, bundles, request, *, current=True):
    require(meta["research_project_id"] == request.research_project_id, "PROJECT_MISMATCH")
    require(not current or meta["project_revision"] == request.project_revision, "REVISION_CONFLICT")
    parent = next((b for b in bundles if b[1] == request.refs.bundle), None)
    require(parent is not None and parent[2] <= request.project_revision, "CONTRACT_BINDING_MISMATCH")
    # Candidate admission must refer to the currently frozen bundle, not an older policy.
    require(not current or parent[1] == bundles[-1][1], "STALE_CONTRACT")
    validate_parent(parent[0], request)
    return parent[0]


def _records(events):
    return [event["candidate"] for event in events if event["kind"] == "CANDIDATE_PUBLICATION_OBSERVED"]


def _recheck(workspace, record, bundle, *, current_revision, bundles, replayed=False):
    request = validate_record(record, bundle)
    root, binding = _workspace(workspace)
    require(binding == record["workspace_binding"] and request.workspace_id == workspace.workspace_id,
            "WORKSPACE_IDENTITY_MISMATCH")
    output = root / "staging" / request.output_identity
    store._path(output)
    require({p.name for p in output.iterdir()} == {"INCOMPLETE.json", "candidate.txt"},
            "OUTPUT_CONTAMINATED")
    expected_marker = canonical_json({"request_digest": digest_bytes(request.canonical_bytes()),
                                     "candidate_id": request.candidate_id})
    require(_read_bytes(output / "INCOMPLETE.json") == expected_marker, "OUTPUT_CONTAMINATED")
    baseline = _read_bytes(root / request.source_filename)
    artifact = _read_bytes(output / "candidate.txt")
    actual = check_diff(baseline, artifact, request, bundle)
    require(actual == record["manifest"], "STAGED_FILE_MISMATCH")
    return {"admissibility": "PERMITTED", "reason": "MODEL_MUTATION_PERMITTED_ONLY",
            "candidate": record, "replayed": replayed, "execution_authorized": False,
            "contract_revision": next(b[2] for b in bundles if b[1] == request.refs.bundle),
            "candidate_project_revision": request.project_revision, "current_project_revision": current_revision,
            "scope": "CURRENT_CONTRACT_MUTATION" if bundles[-1][1] == request.refs.bundle
            else "HISTORICAL_MUTATION"}


def propose_mutation(project, workspace, request):
    """Explicit writes only; a DB observation plus live recheck is required for PERMITTED."""
    try:
        require(type(project) is store.ResearchProject and project._write_enabled, "READ_ONLY")
        require(type(request) is MutationRequest, "INVALID_TYPE")
        request = MutationRequest.from_dict(asdict(request))
        root, binding = _workspace(workspace)
        require(request.workspace_id == workspace.workspace_id, "WORKSPACE_IDENTITY_MISMATCH")
        with project._snapshot(write=True) as (connection, meta, bundles, events):
            records = _records(events)
            previous = next((r for r in records
                             if r["request"]["idempotency_key"] == request.idempotency_key), None)
            if previous:
                require(previous["request"] == asdict(request), "IDEMPOTENCY_CONFLICT")
                bundle = _parent(meta, bundles, request, current=False)
                try:
                    return _recheck(workspace, previous, bundle, current_revision=meta["project_revision"],
                                    bundles=bundles, replayed=True)
                except (ContractError, store.ProjectError, OSError):
                    return {"admissibility": "INCONCLUSIVE", "reason": "PUBLISHED_FILE_UNAVAILABLE",
                            "execution_authorized": False}
            bundle = _parent(meta, bundles, request)
            require(all(r["request"]["candidate_id"] != request.candidate_id
                        and (r["request"]["workspace_id"], r["request"]["output_identity"])
                        != (request.workspace_id, request.output_identity) for r in records),
                    "CANDIDATE_IDENTITY_CONFLICT")
            before = _read_bytes(root / request.source_filename)
            after = edit_scalar(before, request)
            manifest = check_diff(before, after, request, bundle)
            record = {"schema_version": "candidate-publication-v1", "request": asdict(request),
                      "manifest": manifest, "workspace_binding": binding}
            validate_record(record, bundle)
            output = root / "staging" / request.output_identity
            store._path(output, exists=False)
            require(not output.exists(), "OUTPUT_EXISTS")
            _fault("before_stage")
            require(_workspace(workspace) == (root, binding), "WORKSPACE_IDENTITY_MISMATCH")
            output.mkdir()
            _exclusive_file(output / "INCOMPLETE.json", canonical_json({
                "request_digest": digest_bytes(request.canonical_bytes()),
                "candidate_id": request.candidate_id}))
            _fault("after_partial_file")
            _exclusive_file(output / "candidate.txt", after)
            _fault("after_file")
            _recheck(workspace, record, bundle, current_revision=meta["project_revision"], bundles=bundles)
            store._append_audit(connection, "CANDIDATE_PUBLICATION_OBSERVED",
                                request.project_revision, request.refs.bundle,
                                metadata_digest=digest_bytes(canonical_json(record)), candidate=record)
            _fault("before_commit")
            _recheck(workspace, record, bundle, current_revision=meta["project_revision"], bundles=bundles)
            connection.commit()
            _fault("after_commit")
            # Always verify again after commit; a persistent record alone never grants admission.
            try:
                return _recheck(workspace, record, bundle, current_revision=meta["project_revision"], bundles=bundles)
            except (ContractError, store.ProjectError, OSError):
                return {"admissibility": "INCONCLUSIVE", "reason": "PUBLISHED_FILE_UNAVAILABLE",
                        "execution_authorized": False}
    except (ContractError, store.ProjectError, OSError) as exc:
        result = rejection(exc)
        if isinstance(exc, store.ProjectError) and exc.code == "STORE_BUSY":
            result.update(admissibility="INCONCLUSIVE", reason="STORE_BUSY")
        return result


def inspect_candidate(project, workspace, candidate_id):
    try:
        identifier(candidate_id, "candidate")
        with project._snapshot() as (_, meta, bundles, events):
            record = next((r for r in _records(events) if r["request"]["candidate_id"] == candidate_id), None)
            require(record is not None, "CANDIDATE_NOT_FOUND")
            request = validate_record(record, _parent(meta, bundles,
                MutationRequest.from_dict(record["request"]), current=False))
            return _recheck(workspace, record, _parent(meta, bundles, request, current=False),
                            current_revision=meta["project_revision"], bundles=bundles)
    except (ContractError, store.ProjectError, OSError):
        return {"admissibility": "INCONCLUSIVE", "reason": "CANDIDATE_NOT_PROVEN",
                "execution_authorized": False}
