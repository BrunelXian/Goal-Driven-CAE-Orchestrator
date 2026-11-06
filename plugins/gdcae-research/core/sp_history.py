"""Bounded SP historical-data adapter. No solver, external scripts, or ODB reader."""
import bisect
import csv
import hashlib
import io
import json
import math
from pathlib import Path

POLICY = 'run/run_015/artifacts/private/blind_holdout_access_policy.json'
PREAMBLE = ('AGENTS.md', 'docs/Blind_Inversion_Protocol.md', POLICY)
OLD = 'run/run_005/artifacts/'
NEW = 'run/run_014/artifacts/odb/'
BASE_INP = 'CAE/Models/Sanity/Job-1.inp'
CAND_INP = 'run/run_008/artifacts/candidate_inp/SPIO_R008_Q200_N010_Candidate/SPIO_R008_Q200_N010_Candidate.inp'
ALLOW = frozenset(PREAMBLE + (
    OLD+'manifest.json', OLD+'extraction_metadata.json',
    OLD+'file_inventory.json', OLD+'punch_force_displacement.csv',
    OLD+'punch_rp_history_raw.csv', NEW+'manifest.json',
    NEW+'preflight_read.json', NEW+'result.json',
    NEW+'punch_force_displacement.csv', NEW+'punch_history_raw.csv',
    BASE_INP, CAND_INP, 'status/PROJECT_STATUS.md', 'run/README.md',
    'run/run_063/summary.md', 'run/run_064/summary.md', 'run/run_064/run.json'))

class EvidenceError(ValueError):
    pass

def require(condition, code):
    if not condition:
        raise EvidenceError(code)

def sha(data):
    return hashlib.sha256(data).hexdigest()

class Reader:
    """Exact allowlist, reparse refusal, bounded reads. Never enumerates project files."""
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.log = {}
        self.sealed = []
        self.ready = False
        for name in PREAMBLE:
            self.read(name, preamble=True)
        policy = json.loads(self.read(POLICY, preamble=True))
        require(policy.get('policy') == 'NO_CONTENT_ACCESS_OR_USE_UNTIL_EXPLICIT_USER_UNBLIND_AUTHORIZATION', 'POLICY_UNRECOGNIZED')
        self.sealed = [policy['sealed_source']] + policy['sealed_paths']
        self.ready = True

    def path(self, name):
        require(name in ALLOW, 'PATH_NOT_ALLOWLISTED')
        require(name == POLICY or not any(x in ('private', 'references_private') for x in Path(name).parts), 'PRIVATE_CONTENT_DENIED')
        require(name == POLICY or not any(name.casefold().startswith(x.casefold()) for x in self.sealed), 'SEALED_CONTENT_DENIED')
        path = self.root / name
        for part in (path, *path.parents):
            require(not part.is_symlink() and not part.is_junction(), 'REPARSE_POINT_DENIED')
        require(path.resolve().is_relative_to(self.root.resolve()), 'PATH_ESCAPE')
        return path

    def read(self, name, preamble=False):
        require(self.ready or (preamble and name in PREAMBLE), 'POLICY_NOT_READ')
        path = self.path(name)
        before = path.stat()
        require(before.st_size <= 8_000_000, 'INPUT_TOO_LARGE')
        with path.open('rb') as stream:
            data = stream.read(8_000_001)
        after = path.stat()
        require(len(data) <= 8_000_000 and (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'INPUT_CHANGED_DURING_READ')
        digest = sha(data)
        require(name not in self.log or self.log[name]['sha256'] == digest, 'INPUT_CHANGED_BETWEEN_READS')
        self.log[name] = {'sha256': digest, 'size': len(data)}
        return data.decode('utf-8-sig')

    def document(self, name):
        return json.loads(self.read(name))

    def public_record(self, name, manifest):
        records = [x for x in manifest['files'] if x['path'] == name]
        require(len(records) == 1, 'MANIFEST_ENTRY_MISSING_OR_DUPLICATE')
        record = records[0]
        require(record.get('visibility') == 'public' or record.get('private') is False, 'PUBLIC_PROVENANCE_REQUIRED')
        data = self.read(name)
        require(self.log[name]['sha256'] == record['sha256'], 'PROVENANCE_HASH_MISMATCH:'+name)
        return data

def numeric(value):
    result = float(value)
    require(math.isfinite(result), 'NONFINITE_VALUE')
    return result

def curve(text, raw_text, old=False):
    time = 'step_time' if old else 'step_time_model'
    u = 'U2_model_length' if old else 'U2_raw_model_length'
    f = 'RF2_model_force' if old else 'RF2_raw_model_force'
    cols = ['step', time, 'displacement_model_length', 'force_model_force']
    rawcols = ['step', 'history_region', time, u, f] if old else ['step', time, u, f]
    reader = csv.DictReader(io.StringIO(text))
    rawreader = csv.DictReader(io.StringIO(raw_text))
    require(reader.fieldnames == cols and rawreader.fieldnames == rawcols, 'CSV_SCHEMA_MISMATCH')
    rows, rawrows = list(reader), list(rawreader)
    require(len(rows) == len(rawrows) and 2 <= len(rows) <= 100000, 'SAMPLE_COUNT_INVALID')
    points = []
    times = []
    for row, raw in zip(rows, rawrows):
        require(None not in row and None not in raw, 'CSV_ROW_WIDTH')
        require(row['step'] == raw['step'] == 'Step_Punch_Displacement', 'STEP_MISMATCH')
        if old:
            require(raw['history_region'] == 'Node ASM_SPT.1', 'REGION_MISMATCH')
        t, rt = numeric(row[time]), numeric(raw[time])
        d, force = numeric(row[cols[2]]), numeric(row[cols[3]])
        require(t == rt and d == -numeric(raw[u]) and force == -numeric(raw[f]), 'SIGN_OR_SAMPLING_MISMATCH')
        points.append((d, force))
        times.append(t)
    require(all(b > a for a, b in zip(times, times[1:])), 'NONMONOTONIC_TIME')
    require(all(b[0] > a[0] for a, b in zip(points, points[1:])), 'NONMONOTONIC_DISPLACEMENT')
    require(points[0][0] == 0 and times[0] == 0, 'NONZERO_START')
    return points

def compare(old, new):
    xs = [x[0] for x in old]
    require(new[0][0] >= xs[0] and new[-1][0] <= xs[-1], 'INTERPOLATION_OUT_OF_RANGE')
    require(new[-1][0] == xs[-1], 'ENDPOINT_TRAVEL_MISMATCH')
    differences = []
    for d, force in new:
        i = min(max(bisect.bisect_right(xs, d), 1), len(xs)-1)
        x0, y0 = old[i-1]
        x1, y1 = old[i]
        ref = y0 + (y1-y0)*(d-x0)/(x1-x0)
        differences.append((d, force, ref, force-ref))
    peak = max(differences, key=lambda x: abs(x[3]))
    endpoint = differences[-1][3]
    return {
        'baseline_samples': len(old), 'candidate_samples': len(new),
        'baseline_endpoint_force': old[-1][1], 'candidate_endpoint_force': new[-1][1],
        'endpoint_difference': endpoint,
        'endpoint_difference_percent': 100*endpoint/old[-1][1] if old[-1][1] else None,
        'equal_candidate_sample_rms_difference': math.sqrt(sum(x[3]**2 for x in differences)/len(differences)),
        'max_abs_difference': abs(peak[3]), 'max_difference_at_displacement': peak[0],
        'max_difference_at_travel_fraction': peak[0]/new[-1][0],
        'travel': new[-1][0],
        'method': 'Linear interpolation of baseline onto candidate samples; no extrapolation; RMS is equal-sample, not displacement-integral weighted.',
        'units': {'displacement':'model_length','force':'model_force','time':'model_time','physical_unit_verification':'UNVERIFIED'},
    }, differences

def model(text):
    # Abaqus comment lines are not solver cards. Report their differences separately.
    lines = [line+'\n' for line in text.splitlines()]
    plastic, residual, blocks = [], [], []
    active = None
    plastic_count = 0
    comments = []
    for line in lines:
        if line.startswith('**'):
            comments.append(line.rstrip())
            continue
        if line.startswith('*') and not line.startswith('**'):
            keyword = line.strip().split(',')[0].casefold()
            require(keyword != '*include', 'INCLUDE_NOT_SUPPORTED')
            active = keyword
            blocks.append({'header':line.strip(), 'data':[]})
            if keyword == '*plastic':
                plastic_count += 1
        if active == '*plastic' and not line.startswith('*') and line.strip():
            values = [numeric(v.strip()) for v in line.split(',')]
            require(len(values) == 2, 'PLASTIC_TABLE_SCHEMA')
            plastic.append(values)
        else:
            residual.append(line)
        if blocks and not line.startswith('*') and line.strip():
            blocks[-1]['data'].append(line.strip())
    require(plastic_count == 1 and len(plastic) >= 2, 'SINGLE_PLASTIC_TABLE_REQUIRED')
    require(all(b[1] > a[1] for a,b in zip(plastic, plastic[1:])), 'PLASTIC_STRAIN_NOT_INCREASING')
    selected = ('*elastic','*material','*element','*boundary','*friction','*surface behavior','*static','*step','*solid section','*contact pair')
    settings = []
    for block in blocks:
        key = block['header'].split(',')[0].casefold()
        if key in selected:
            settings.append({'header':block['header'], 'data':block['data'] if key != '*element' else {'rows':len(block['data'])}})
    return {'plastic_rows':len(plastic), 'plastic_first':plastic[0], 'plastic_last':plastic[-1],
            'plastic_columns':['stress_model_units','equivalent_plastic_strain'],
            'nonplastic_sha256':sha(''.join(residual).encode()), 'settings':settings, 'comments':comments}

def analyze(project_root):
    r = Reader(project_root)
    # Metadata first; never follow its private evidence links or execute referenced scripts.
    for name in ('status/PROJECT_STATUS.md','run/README.md','run/run_064/run.json','run/run_064/summary.md','run/run_063/summary.md'):
        r.read(name)
    old_manifest = r.document(OLD+'manifest.json')
    new_manifest = r.document(NEW+'manifest.json')
    metadata = json.loads(r.public_record(OLD+'extraction_metadata.json', old_manifest))
    inventory = json.loads(r.public_record(OLD+'file_inventory.json', old_manifest))
    preflight = json.loads(r.public_record(NEW+'preflight_read.json', new_manifest))
    result = json.loads(r.public_record(NEW+'result.json', new_manifest))
    require(metadata['selected_step'] == 'Step_Punch_Displacement' and metadata['selected_history_region'] == 'Node ASM_SPT.1', 'SELECTOR_MISMATCH')
    require(inventory['selected_group'] == 'Sanity', 'BASELINE_GROUP_MISMATCH')
    require(result['extraction_status'] == 'PASS' and preflight['safe_to_open'] is True, 'HISTORICAL_EXTRACTION_NOT_ACCEPTED')
    require(result['task_id'] == preflight['task_id'] and result['job_name'] == preflight['job_name'], 'PROVENANCE_IDENTITY_MISMATCH')
    require(result['odb_sha256'] == preflight['odb_before']['sha256'] == preflight['odb_after']['sha256'], 'HISTORICAL_ODB_IDENTITY_MISMATCH')
    old = curve(r.public_record(OLD+'punch_force_displacement.csv', old_manifest), r.public_record(OLD+'punch_rp_history_raw.csv', old_manifest), old=True)
    new = curve(r.public_record(NEW+'punch_force_displacement.csv', new_manifest), r.public_record(NEW+'punch_history_raw.csv', new_manifest))
    require(len(old) == metadata['samples'] and len(new) == result['sample_count'], 'PROVENANCE_SAMPLE_COUNT_MISMATCH')
    require(r.log[OLD+'punch_force_displacement.csv']['sha256'] == result['historical_csv_sha256'], 'BASELINE_CSV_IDENTITY_MISMATCH')
    baseline_model = model(r.read(BASE_INP))
    candidate_model = model(r.read(CAND_INP))
    require(r.log[CAND_INP]['sha256'] == result['inp_sha256'] == preflight['inp_sha256'], 'INP_IDENTITY_MISMATCH')
    require(baseline_model['nonplastic_sha256'] == candidate_model['nonplastic_sha256'], 'NONPLASTIC_MODEL_CHANGED')
    metrics, differences = compare(old, new)
    report = {
        'schema':'gdcae-sp-history-v1', 'status':'COMPUTED_WITH_LIMITATIONS',
        'scope':'Adapted SP Sanity versus run_014 historical public CSV; no new execution or ODB extraction.',
        'model':{'baseline':baseline_model,'candidate':candidate_model,
                 'nonplastic_invariant':'Exact non-comment text equality after newline normalization outside the single plastic data block; includes mesh, geometry, contact, clamps, loading, elasticity and output settings. Comments are recorded separately and excluded from solver-card comparison.',
                 'baseline_binding_limit':'Current Sanity INP compared directly; full historical baseline INP/ODB source chain is in private inventory and was not opened. Public group/CSV records are verified, not the sealed source chain.'},
        'metrics':metrics,
        'provenance':{k:result[k] for k in ('task_id','queue_id','job_name','project_id','execution_status','extraction_status','science_status','odb_sha256','inp_sha256','runner_full_process_aggregation')},
        'odb_limit':'Existing public extraction provenance only; ODB contents were not opened, hashed, or re-extracted. Historical ODB digest is a recorded claim, not freshly verified.',
        'decision':{'material_acceptance':'NOT_ESTABLISHED', 'reason':'A nearly matching endpoint does not establish full-curve equality, unique parameters, experimental agreement, or physical material validity. No acceptance tolerance or authorized experimental data were supplied.',
                    'experimental_loss':None, 'physical_validation':'NOT_EVALUATED'},
        'next_validation':{'proposal':'Based on run_063 public coupling summary and run_064 current public status: preregister one weak-direction plus/minus mixed-parameter two-point mechanism study, with numerical-resolution criteria and whole-curve stage comparisons. Obtain separate execution authorization; this cannot replace converged numerical certification.',
                           'execution_authorized':False,'new_FE_calls':0,
                           'status_sources':['run/run_063/summary.md','run/run_064/summary.md']},
        'privacy':{'prior_exposure':'COMPROMISED_BY_PRIOR_EXPOSURE (project protocol); no strict-blind claim',
                   'private_content_read':False,'access_policy_metadata_read':True},
        'inputs':r.log,
    }
    # Detect changes between use and completion without scanning or opening any other path.
    for name in tuple(r.log):
        r.read(name)
    return report, differences

def markdown(report):
    m = report['metrics']
    return '\n'.join([
        '# GDCAE SP historical comparison', '',
        'Material acceptance: **NOT ESTABLISHED**. This is a model-to-model historical comparison.', '',
        f"Samples: baseline {m['baseline_samples']}; candidate {m['candidate_samples']}.",
        f"Endpoint difference: {m['endpoint_difference']:.12g} model force ({m['endpoint_difference_percent']:.9g}%).",
        f"Full-curve RMS: {m['equal_candidate_sample_rms_difference']:.12g}; maximum absolute difference: {m['max_abs_difference']:.12g} model force, at {m['max_difference_at_travel_fraction']:.6%} of travel.",
        '', m['method'], 'Signs: displacement = -U2; force = -RF2. No absolute value, shift, smoothing or 2π scaling. Physical units remain unverified.', '',
        report['model']['nonplastic_invariant'], report['model']['baseline_binding_limit'], '',
        report['decision']['reason'], report['odb_limit'],
        'Historical execution: '+report['provenance']['execution_status']+'; process aggregation: '+report['provenance']['runner_full_process_aggregation']+'.', '',
        report['next_validation']['proposal'], '',
        'No solver, ODB reader, SP script, private experiment or sealed tensile data was used. Prior project exposure remains disclosed. See report.json for source hashes and material/settings details.', ''])
