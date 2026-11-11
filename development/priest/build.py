"""Build an independent Priest ZIP, checking all prior agent integrity hashes."""
import hashlib
import json
from pathlib import Path
import zipfile

from hs_arena.deck import validate_deck_data
from development.benchmarks.run import fingerprint


def main():
    root = Path(__file__).resolve().parents[2]
    source = root/"control_priest"
    protected = json.loads((root/"development/priest/protected-before.json").read_text())
    for name, sha in protected.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == sha, name
    selection = json.loads((root/"development/priest/selection.json").read_text())
    assert fingerprint(source) == selection["code_sha256"] == fingerprint(root/selection["path"])
    assert not validate_deck_data(json.loads((source/"deck.json").read_text()))
    files = sorted(p for p in source.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    assert all(p.suffix in {".py", ".md", ".json"} for p in files)
    size = sum(p.stat().st_size for p in files)
    assert size < 10_000_000
    target = root/"dist/hearthstone-control-priest.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in files:
            entry = zipfile.ZipInfo(str(Path("control_priest")/path.relative_to(source)), date_time=(2026, 11, 10, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED; entry.external_attr = 0o100644 << 16
            z.writestr(entry, path.read_bytes())
    result = {"source": "control_priest", "source_sha256": fingerprint(source), "archive": str(target.relative_to(root)),
              "archive_bytes": target.stat().st_size, "uncompressed_bytes": size,
              "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "protected_files_unchanged": len(protected),
              "files": {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (root/"dist/hearthstone-control-priest.manifest.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k != "files"}, indent=2))


if __name__ == "__main__":
    main()
