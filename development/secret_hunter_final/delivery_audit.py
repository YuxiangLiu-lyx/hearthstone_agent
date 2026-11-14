"""Validate the one delivered ZIP and record the frozen selection outcome."""
import hashlib
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile

from development.benchmarks.run import fingerprint
from development.secret_hunter_final.audit import deck_audit
from development.secret_hunter_final.study import ROOT, RUN, HERE
from development.secret_hunter_mcgs import train


def main():
    doc = ROOT / 'docs/secret_hunter_final'
    recommendation = json.loads((doc / 'recommendation.json').read_text())
    runtime = json.loads((doc / 'runtime.json').read_text())
    mcp = json.loads((doc / 'mcp-audit.json').read_text())
    path = Path(recommendation['zip'])
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == recommendation['zip_sha256']
    assert path.stat().st_size == recommendation['bytes'] <= 10_000_000
    assert Path(runtime['candidate']).resolve() == (ROOT / recommendation['final_exact_unpacked_path']).resolve()
    assert runtime['invalid'] == runtime['over_2s'] == runtime['ordinary_fallbacks'] == 0
    assert mcp['games'] == 6
    assert mcp['envelope_mismatches'] == mcp['illegal'] == mcp['timeouts'] == mcp['forfeits'] == 0
    assert all(r['source_sha256'] == recommendation['source_sha256'] for r in mcp['records'])
    with tempfile.TemporaryDirectory(prefix='krush-delivery-') as temporary:
        with ZipFile(path) as archive:
            members = archive.namelist()
            assert {Path(n).parts[0] for n in members} == {'secret-hunter'}
            assert 'secret-hunter/SKILL.md' in members
            assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in members)
            assert all(Path(n).suffix in ('.py', '.json', '.md') for n in members)
            expanded_bytes = sum(info.file_size for info in archive.infolist())
            assert expanded_bytes <= 10_000_000
            archive.extractall(temporary)
        source = Path(temporary) / 'secret-hunter'
        assert fingerprint(source) == recommendation['source_sha256']
        audit = deck_audit(source)
    record = {'zip': str(path), 'zip_sha256': digest, 'bytes': path.stat().st_size,
              'expanded_bytes': expanded_bytes, 'members': members,
              'fresh_extraction_deck_and_cli_audit': audit,
              'runtime_and_official_mcp_match_recommended_source': True,
              'submitted': False}
    train.atomic(doc / 'delivery-audit.json', record)
    lineage_path = HERE / 'lineage.json'
    lineage = json.loads(lineage_path.read_text())
    for candidate in lineage:
        if candidate['name'] == recommendation['recommended']:
            candidate['status'] = 'recommended: completed frozen whole-game, actual CLI and official no-model MCP checks'
        elif candidate['name'] == recommendation['challenger']:
            candidate['status'] = 'not promoted: independent final evidence failed the preregistered gate; immutable capability branch retained'
        if candidate['name'] in ('B', recommendation['challenger']):
            candidate['final_validation'] = 'docs/secret_hunter_final/recommendation.json'
    train.atomic(lineage_path, lineage)
    db = train.connect(RUN)
    train.setmeta(db, 'recommended', recommendation['recommended'])
    db.close()
    print(json.dumps({k: v for k, v in record.items() if k not in ('members', 'fresh_extraction_deck_and_cli_audit')}))


if __name__ == '__main__':
    main()
