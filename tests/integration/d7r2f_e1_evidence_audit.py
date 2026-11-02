"""Bounded read-only incident preservation/reference audit; no application imports.

Only aggregate counts and digests leave this script. No historical report text,
credential bytes, Grant IDs or Project IDs are emitted or copied.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import zipfile

GD = Path('D:/Projects/Goal-Driven-CAE-Orchestrator')
AF = Path('D:/Projects/abqjobpilot_dev')
LOCAL = Path('C:/Users/wuxia/AppData/Local')
BASE = LOCAL / 'GDCAE-G3-D3-OFFLINE-20261030-A01/D6-20261031-A01/gdcae-m03f1p1-g2long-d6'
INCIDENT = BASE / 'af-d7r2f-selection-01-temp'
R2 = LOCAL / 'Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/GDCAE-D7-R2-20261101-A01'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def files(root):
    assert root.is_dir()
    result = []
    for path in root.rglob('*'):
        assert not path.is_symlink() and not path.is_junction()
        if path.is_file():
            result.append(path)
    return sorted(result)


def closure(root, paths):
    rows = [(p.relative_to(root).as_posix(), 'sha256:' + digest(p.read_bytes())) for p in paths]
    return digest(json.dumps(sorted(rows), separators=(',', ':')).encode())


def main():
    phase = sys.argv[1]
    assert phase in {'before', 'after'}
    destination = BASE / ('af-e1-incident-' + phase + '.safe.json')
    assert not destination.exists()
    incident_files = files(INCIDENT)
    databases = [p for p in incident_files if p.name == 'execution.sqlite3']
    assert len(databases) == 32
    counts = {}
    runs = plans = invalid_bindings = 0
    needles = {INCIDENT.name.encode(), str(INCIDENT).encode(), str(INCIDENT.resolve()).encode()}
    for path in databases:
        # No Store imports, normal SQLite connection, recovery, or mutation.
        conn = sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
        try:
            for table in ('grants', 'runs', 'plans'):
                for (body,) in conn.execute('SELECT body FROM ' + table):
                    row = json.loads(body)
                    for key in ('grant_id', 'run_id', 'project_instance_id', 'plan_id'):
                        value = row.get(key)
                        if isinstance(value, str) and len(value) >= 12:
                            needles.add(value.encode())
                    if table == 'grants':
                        kind = row.get('grant_kind', 'MISSING')
                        counts[kind] = counts.get(kind, 0) + 1
                    elif table == 'runs':
                        runs += 1
                    else:
                        plans += 1
                        config = row.get('runtime_binding', {})
                        if isinstance(config, str):
                            config = json.loads(config)
                        if not all(key in config for key in ('backend_id', 'backend_version',
                                                             'entry', 'cmd', 'materials')):
                            invalid_bindings += 1
        finally:
            conn.close()
    references = 0
    checked = 0

    def inspect(blob):
        nonlocal references, checked
        checked += 1
        references += int(any(needle in blob for needle in needles))

    # Exact D7 candidates and nonexecuting A packet; no general history scan.
    candidate = GD / 'dist/D7-R1_OFFLINE_SOURCE_CANDIDATE_20261101'
    targets = files(candidate) + files(R2 / 'wheels') + [R2 / 'candidate.json',
        R2 / 'A_ONLY_NONEXECUTING_REVIEW_PACKET.json']
    for path in targets:
        inspect(path.name.encode())
        if path.suffix in {'.zip', '.whl'}:
            with zipfile.ZipFile(path) as archive:
                for entry in archive.infolist():
                    assert entry.file_size <= 16 * 1024 * 1024
                    inspect(entry.filename.encode())
                    if not entry.is_dir():
                        inspect(archive.read(entry))
        else:
            inspect(path.read_bytes())
    closures = {}
    for name, root in [('gd_src', GD / 'src'), ('af_src', AF / 'abqjobpilot'),
                       ('plugin_v2', GD / 'plugins/gdcae-d7'), ('plugin_v1', GD / 'plugins/gdcae')]:
        paths = [p for p in files(root) if '__pycache__' not in p.parts and p.suffix != '.pyc']
        closures[name] = closure(root, paths)
        for path in paths:
            inspect(path.read_bytes())
    report = {'schema': 'd7r2f-e1-bounded-audit-v1', 'phase': phase,
              'incident': {'databases': len(databases), 'grant_types': counts, 'runs': runs,
                           'plans': plans, 'incomplete_runtime_bindings': invalid_bindings,
                           'owner_json': sum(p.name == 'owner.json' for p in incident_files),
                           'file_count': len(incident_files),
                           'file_closure_sha256': closure(INCIDENT, incident_files)},
              'reference_scan': {'checked_objects': checked, 'matches': references,
                                 'scope': 'D7 R1/R2 artifacts, A preview, current GD/AF sources and plugin v1/v2'},
              'source_closures': closures}
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
