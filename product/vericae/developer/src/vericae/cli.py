"""The sole VeriCAE command: read local files and report consistency only."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import stat
from urllib.parse import unquote

import yaml

DOCUMENT_LIMIT = 1024 * 1024
FRONTMATTER_LIMIT = 65536
CARD = 'research/RESEARCH_CARD.md'
REQUIRED_FILES = ('README.md', CARD, 'research/TASK_CARDS.md',
                  'models/SANITY_MODEL_SPEC.md', 'docs/initiation/HANDOFF.md',
                  '.abqjobpilot/link.json')
REQUIRED_DIRS = ('research', 'models', 'experiments', 'scripts', 'reports',
                 'docs/initiation', 'docs/research-runs', '.abqjobpilot')
BORDER = '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
MODULES = ('❶ Research Contract', '❷ Research Assumptions', '❸ Model Evolution',
           '❹ Research Subagent', '❺ Research Roadmap', '❻ Next Action')
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z')
SHA256 = re.compile(r'[0-9a-f]{64}\Z')


class _Invalid(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _require(condition, code, message):
    if not condition:
        raise _Invalid(code, message)


def _shape(value, fields):
    _require(type(value) is dict, 'INVALID_TYPE', 'Expected an object.')
    _require(fields.keys() <= value.keys(), 'MISSING_FIELD',
             'Missing required field(s): ' + ', '.join(sorted(fields.keys() - value.keys())))
    _require(value.keys() <= fields.keys(), 'UNKNOWN_FIELD', 'Unexpected field in schema v1.')
    for key, kind in fields.items():
        _require(type(value[key]) is kind, 'INVALID_TYPE', f'{key}: expected {kind.__name__}.')


def _text(value):
    return type(value) is str and 0 < len(value.strip()) <= 256


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _require(type(key) is str, 'INVALID_TYPE', 'Object keys must be strings.')
        _require(key not in result, 'DUPLICATE_KEY', 'Duplicate mapping key.')
        result[key] = value
    return result


class _YamlLoader(yaml.SafeLoader):
    """Safe tags, with duplicate keys rejected instead of silently overwritten."""


def _mapping(loader, node):
    return _unique((loader.construct_object(k), loader.construct_object(v)) for k, v in node.value)


_YamlLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _frontmatter(text):
    lines = text.splitlines(keepends=True)
    _require(lines and lines[0].strip() == '---', 'YAML_FRONTMATTER',
             'Research Card must start with YAML frontmatter.')
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
    _require(end is not None, 'YAML_FRONTMATTER', 'Missing closing frontmatter delimiter.')
    source = ''.join(lines[1:end])
    _require(len(source.encode('utf-8')) <= FRONTMATTER_LIMIT, 'DOCUMENT_TOO_LARGE',
             'YAML frontmatter exceeds 64 KiB.')
    for token in yaml.scan(source):
        _require(not isinstance(token, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken)),
                 'YAML_ALIAS_FORBIDDEN', 'YAML anchors and aliases are not part of schema v1.')
    return yaml.load(source, Loader=_YamlLoader), ''.join(lines[end + 1:])


def _card_schema(data):
    _shape(data, {'schema_version': int, 'project_name': str, 'revision': int, 'phase': str,
                  'main_writer': str, 'model': dict, 'references': list, 'receipts': list})
    _require(data['schema_version'] == 1, 'SCHEMA_VERSION', 'Supported schema_version is 1.')
    _require(data['revision'] >= 1, 'INVALID_VALUE', 'revision must be positive.')
    _require(_text(data['project_name']) and _text(data['main_writer']), 'INVALID_VALUE',
             'project_name and main_writer must be nonempty text up to 256 characters.')
    _require(data['phase'] in {'PLANNING', 'INVESTIGATION', 'REVIEW', 'PAUSED', 'COMPLETE'},
             'INVALID_VALUE', 'Unknown descriptive research phase.')
    _shape(data['model'], {'path': str, 'version': str, 'qualification': str})
    _require(_text(data['model']['version']), 'INVALID_VALUE', 'model.version must be text.')
    _require(data['model']['qualification'] in {'UNVERIFIED', 'IN_REVIEW', 'QUALIFIED_FOR_SCOPE'},
             'INVALID_VALUE', 'Unknown descriptive model qualification.')
    for name in ('references', 'receipts'):
        _require(len(data[name]) <= 1024, 'INVALID_VALUE', 'Too many reference entries.')
        for entry in data[name]:
            fields = {'path': str, 'sha256': str}
            if name == 'receipts':
                fields.update(receipt_id=str, run_id=str)
            _shape(entry, fields)
            _require(bool(SHA256.fullmatch(entry['sha256'])), 'INVALID_DIGEST',
                     'sha256 must contain 64 lowercase hexadecimal characters.')
            if name == 'receipts':
                _require(all(IDENTIFIER.fullmatch(entry[k]) for k in ('receipt_id', 'run_id')),
                         'INVALID_IDENTIFIER', 'Receipt and Run IDs must be bounded identifiers.')
    return True


def _visible_lines(text):
    fence = None
    for line in text.splitlines():
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            token = marker[1][0]
            fence = None if fence == token else (token if fence is None else fence)
        elif fence is None:
            yield line


def _layout(body):
    lines = list(_visible_lines(body))
    headings = [line[4:] for line in lines if line.startswith('### ')]
    _require(headings == [*MODULES, '💬 Codex · 工作回复'], 'CARD_LAYOUT',
             'Keep all six ordered modules and the separate Codex work reply.')
    borders = [i for i, line in enumerate(lines) if line == BORDER]
    _require(len(borders) == 2, 'CARD_LAYOUT', 'Keep the two original card borders.')
    _require(lines[borders[0] + 1:borders[1]].count(
        '## ⚛️ CAE Agent · Research Workspace') == 1, 'CARD_LAYOUT', 'Keep the card title.')
    heading_positions = [i for i, line in enumerate(lines) if line.startswith('### ')]
    _require(borders[0] < heading_positions[0] < heading_positions[-2] < borders[1]
             < heading_positions[-1], 'CARD_LAYOUT', 'Modules belong inside the card borders.')
    section = lines[heading_positions[3]:heading_positions[4]]
    previous = None
    for header in ('| 🧠 **Main Agent** | ⚙️ **CAE Subagent** |',
                   '| 📊 **Results Subagent** | 🛡️ **Independent Validation** |'):
        _require(header in section, 'CARD_LAYOUT', 'Keep both tables inside Research Subagent.')
        position = section.index(header)
        _require(len(section) > position + 3 and section[position + 1] == '| --- | --- |'
                 and all(section[i].startswith('|') for i in (position + 2, position + 3)),
                 'CARD_LAYOUT', 'Each role table needs a separator, responsibilities and statuses.')
        if previous is not None:
            _require(position > previous + 3 and '' in section[previous + 4:position],
                     'CARD_LAYOUT', 'Keep a blank line between the two role tables.')
        previous = position


def _not_reparse(path):
    info = path.lstat()
    _require(not stat.S_ISLNK(info.st_mode) and not (
        getattr(info, 'st_file_attributes', 0) & 0x400),
        'UNSAFE_PATH', 'Symlinks and Windows reparse points are not followed.')
    return info


class _Reader:
    """Per-invocation read helpers, with no persistent state or mutation API."""

    def __init__(self, root):
        raw = os.fspath(root)
        _require(type(raw) is str and bool(raw) and len(raw) <= 1024
                 and not any(ord(c) < 32 for c in raw), 'UNSAFE_PATH', 'Invalid project path.')
        _require(not raw.startswith(('\\\\', '//')), 'UNSAFE_PATH', 'UNC roots are not allowed.')
        self.root = Path(os.path.abspath(raw))
        for parent in (*reversed(self.root.parents), self.root):
            info = _not_reparse(parent)
            _require(stat.S_ISDIR(info.st_mode), 'INVALID_ROOT', 'Project root must be a directory.')
        self.files = set()

    def path(self, raw, *, base=None, directory=False):
        _require(type(raw) is str and bool(raw) and len(raw) <= 1024,
                 'UNSAFE_PATH', 'Expected a bounded nonempty relative path.')
        _require(not re.search(r'%(?![0-9a-fA-F]{2})', raw), 'UNSAFE_PATH', 'Invalid URL escape.')
        decoded = unquote(raw, errors='strict')
        _require(not any(ord(c) < 32 for c in decoded)
                 and not any(c in decoded for c in '\\:?#<>"|*'),
                 'UNSAFE_PATH', 'Control characters, backslashes, URI/drive/query syntax are forbidden.')
        _require(not decoded.startswith('/') and not PureWindowsPath(decoded).drive,
                 'UNSAFE_PATH', 'References must be relative local paths.')
        for part in decoded.split('/'):
            if part in ('.', '..'):
                continue
            _require(part and not part.endswith((' ', '.')) and not re.fullmatch(
                r'(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', part),
                'UNSAFE_PATH', 'Invalid or reserved path component.')
        candidate = Path(os.path.abspath((base or self.root) / decoded))
        _require(candidate.is_relative_to(self.root), 'PATH_OUTSIDE_PROJECT',
                 'Reference escapes the project root.')
        relative = candidate.relative_to(self.root)
        for count in range(1, len(relative.parts) + 1):
            path = self.root.joinpath(*relative.parts[:count])
            try:
                info = _not_reparse(path)
            except FileNotFoundError as exc:
                raise _Invalid('MISSING_DIRECTORY' if directory else 'MISSING_FILE',
                               'Referenced local path does not exist.') from exc
            if count < len(relative.parts):
                _require(stat.S_ISDIR(info.st_mode), 'UNSAFE_PATH', 'Parent must be a directory.')
        info = _not_reparse(candidate)
        _require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode),
                 'INVALID_FILE_TYPE', 'Expected a directory.' if directory else 'Expected a regular file.')
        return candidate

    def read(self, raw):
        path = self.path(raw)
        with path.open('rb') as stream:
            data = stream.read(DOCUMENT_LIMIT + 1)
        _require(len(data) <= DOCUMENT_LIMIT, 'DOCUMENT_TOO_LARGE', 'Document exceeds 1 MiB.')
        self.files.add(path)
        return data.decode('utf-8-sig')

    def digest(self, raw):
        path = self.path(raw)
        value = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                value.update(chunk)
        self.files.add(path)
        return value.hexdigest()


def _json(text):
    def reject_constant(_):
        raise _Invalid('JSON_SYNTAX', 'Non-finite JSON constants are forbidden.')
    return json.loads(text, object_pairs_hook=_unique, parse_constant=reject_constant)


def _link_schema(data):
    _require(type(data) is dict, 'INVALID_TYPE', 'link.json must be an object.')
    _require(set(data) == {'schema_version', 'project_id', 'project_instance_id'},
             'LINK_SCHEMA', 'link.json allows only schema_version and two non-sensitive project IDs.')
    _require(type(data['schema_version']) is int and data['schema_version'] == 1,
             'SCHEMA_VERSION', 'link.json schema_version must be integer 1.')
    ids = (data['project_id'], data['project_instance_id'])
    _require(all(x is None for x in ids) or all(
        type(x) is str and IDENTIFIER.fullmatch(x) for x in ids),
        'LINK_SCHEMA', 'Both project IDs must be null (unbound) or bounded strings (references only).')


def _destinations(text):
    # The workspace format supports inline and reference-style local links.
    # Ignore fenced examples; remote http(s) links are never opened or certified.
    for line in _visible_lines(text):
        values = re.findall(r'!?\[[^\]\n]*\]\(([^)\n]*)\)', line)
        definition = re.match(r'^\s*\[[^\]]+\]:\s*(.+)$', line)
        if definition:
            values.append(definition[1])
        for value in values:
            value = value.strip()
            # Optional Markdown titles are not part of the destination.
            match = re.fullmatch(r'(?:<([^>]+)>|(\S+?))(?:\s+[\"\'].*[\"\'])?', value)
            _require(match is not None, 'MARKDOWN_LINK', 'Unsupported or empty link destination.')
            yield match[1] or match[2]


def check_project(project_path):
    """Return a local consistency report. No file, network or process writes."""
    errors = []

    def attempt(location, operation):
        try:
            return operation()
        except _Invalid as exc:
            errors.append({'code': exc.code, 'location': location, 'message': str(exc)})
        except (yaml.YAMLError, json.JSONDecodeError, UnicodeError, RecursionError):
            errors.append({'code': 'DOCUMENT_SYNTAX', 'location': location,
                           'message': 'Invalid, unsupported or excessively nested YAML/JSON/UTF-8.'})
        except OSError:
            errors.append({'code': 'IO_ERROR', 'location': location,
                           'message': 'Cannot read the required local path.'})
        return None

    reader = attempt('ProjectPath', lambda: _Reader(project_path))
    documents = {}
    if reader is not None:
        for directory in REQUIRED_DIRS:
            attempt(directory, lambda d=directory: reader.path(d, directory=True))
        for name in REQUIRED_FILES:
            content = attempt(name, lambda n=name: reader.read(n))
            if content is not None and name.endswith('.md'):
                documents[name] = content
            elif content is not None:
                attempt(name, lambda c=content: _link_schema(_json(c)))
        parsed = attempt(CARD, lambda: _frontmatter(documents[CARD])) if CARD in documents else None
        if parsed is not None:
            data, body = parsed
            attempt(CARD + ':layout', lambda: _layout(body))
            valid = attempt(CARD + ':schema', lambda: _card_schema(data))
            if valid:
                attempt(CARD + ':model.path', lambda: reader.path(data['model']['path']))
                for group in ('references', 'receipts'):
                    seen = set()
                    for index, entry in enumerate(data[group]):
                        def verify(e=entry, kind=group):
                            path = reader.path(e['path'])
                            _require(path not in seen, 'DUPLICATE_REFERENCE', 'Duplicate file reference.')
                            seen.add(path)
                            _require(reader.digest(e['path']) == e['sha256'], 'DIGEST_MISMATCH',
                                     'Referenced bytes do not match recorded SHA-256.')
                            if kind == 'receipts':
                                receipt = _json(reader.read(e['path']))
                                _require(type(receipt) is dict, 'INVALID_TYPE', 'Receipt must be an object.')
                                _require(all(receipt.get(k) == e[k] for k in ('receipt_id', 'run_id')),
                                         'RECEIPT_ID_MISMATCH', 'Local Receipt/Run IDs differ from the reference.')
                            elif path.suffix.lower() == '.md':
                                documents.setdefault(path.relative_to(reader.root).as_posix(),
                                                     reader.read(e['path']))
                        attempt(f'{CARD}:{group}[{index}]', verify)
        # Traverse the explicitly reachable Markdown graph, including Handoff inputs.
        visited = set()
        while documents.keys() - visited:
            name = next(iter(documents.keys() - visited))
            visited.add(name)
            def verify_links(n=name):
                for destination in _destinations(documents[n]):
                    if destination.startswith(('https://', 'http://', '#')):
                        continue
                    raw = destination.split('#', 1)[0]
                    path = reader.path(raw, base=(reader.root / n).parent)
                    reader.files.add(path)
                    if path.suffix.lower() == '.md':
                        rel = path.relative_to(reader.root).as_posix()
                        if rel not in documents:
                            documents[rel] = reader.read(rel)
            attempt(name + ':links', verify_links)
    return {'status': 'FAIL' if errors else 'PASS', 'scope': 'LOCAL_CONSISTENCY_ONLY',
            'receipt_authenticity': 'NOT_VERIFIED', 'execution_authorization': 'NOT_ASSESSED',
            'checked_files': len(reader.files) if reader else 0, 'errors': errors}


def main(argv=None):
    parser = argparse.ArgumentParser(prog='vericae', description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('check', help='Check local workspace consistency without writes.')
    command.add_argument('project_path')
    args = parser.parse_args(argv)
    result = check_project(args.project_path)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result['status'] == 'PASS' else 1
