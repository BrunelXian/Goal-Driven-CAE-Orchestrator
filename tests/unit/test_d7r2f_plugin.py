"""Bounded pure Plugin contract tests; installed acceptance is separately recorded."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


plugin = load(ROOT/'plugins/gdcae-d7/scripts/gdcae.py', 'd7_helper_tests')
builder = load(ROOT/'plugins/gdcae/scripts/candidate.py', 'd7_builder_tests')
legacy = load(ROOT/'plugins/gdcae/scripts/gdcae.py', 'legacy_helper_tests')


def test_separate_identity_and_preserved_legacy():
    files = plugin.package_files()
    assert json.loads(files['plugin.json'])['name'] == 'gdcae-d7'
    assert plugin.PLUGIN_VERSION == '0.1.0-alpha.6-d7r2f'
    assert legacy.validate_package(legacy.read_package())['plugin_version'] == '0.1.0-alpha.5'
    assert builder.VERSION == '0.0.0+g3d6'


def test_wheel_version_and_plugin_closed_payload():
    files = {'src/aegiscae/__init__.py': b'',
             'plugins/gdcae-d7/plugin.json': plugin.package_files()['plugin.json']}
    name, body = builder.wheel_bytes('gdcae', files, version=plugin.VERSION)
    assert '+d7r2f' in name
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        assert z.read('aegiscae/_gdcae_d7_plugin/plugin.json') == files['plugins/gdcae-d7/plugin.json']
        assert b'Version: 0.0.0+d7r2f' in z.read('aegiscae-0.0.0+d7r2f.dist-info/METADATA')
    with pytest.raises(builder.CandidateBlocked, match='UNREVIEWED_VERSION'):
        builder.wheel_bytes('gdcae', files, version='unreviewed')


@pytest.mark.parametrize('command', ['authorize', 'dispatch', 'start-owner', 'submit', 'grant'])
def test_no_execution_command(command, monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['gdcae-d7', command])
    assert plugin.main() == 2
    assert json.loads(capsys.readouterr().out)['code'] == 'INVALID_ARGUMENTS'


def test_atomic_receipt_replay_conflict(tmp_path):
    path = tmp_path/'record.json'
    plugin.write_once(path, {'candidate': 'A'})
    before = path.read_bytes()
    plugin.write_once(path, {'candidate': 'A'})
    with pytest.raises(ValueError, match='IDEMPOTENCY_CONFLICT'):
        plugin.write_once(path, {'candidate': 'B'})
    assert path.read_bytes() == before


def test_old_installed_core_cannot_qualify_d7():
    with pytest.raises((ValueError, ImportError)):
        plugin.qualified()


def test_decline_is_not_af_human_decision_or_refund(tmp_path, monkeypatch):
    view = {'contract_digest': 'sha256:'+'a'*64, 'budget': {'held': 1, 'charged': 0}}
    monkeypatch.setattr(plugin, 'opened', lambda _p: (tmp_path, None, view))
    result = plugin.decline_preview(tmp_path)
    assert result['status'] == 'PREVIEW_DECLINED_NOT_AF_DECISION'
    assert not result['budget_released'] and not result['grant_issued']
    assert plugin.decline_preview(tmp_path) == result
