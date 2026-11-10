"""Create a deterministic, Python-only skill archive and its integrity manifest."""
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    root = Path(__file__).resolve().parents[2]
    source = root/"face_hunter"
    target = root/"dist/face-hunter-agent.zip"
    allowed = {".py", ".md", ".json"}
    paths = sorted(p for p in source.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    assert all(p.suffix in allowed for p in paths), "Unexpected non-source skill artifact"
    size = sum(p.stat().st_size for p in paths)
    assert size < 10_000_000
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            member = zipfile.ZipInfo(str(Path("face_hunter")/path.relative_to(source)), date_time=(2026, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            member.external_attr = 0o644 << 16
            archive.writestr(member, path.read_bytes())
    manifest = {"archive": str(target.relative_to(root)), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "uncompressed_bytes": size, "archive_bytes": target.stat().st_size,
                "files": {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (root/"dist/face-hunter-agent.manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({k:v for k,v in manifest.items() if k != "files"}, indent=2))


if __name__ == "__main__":
    main()
