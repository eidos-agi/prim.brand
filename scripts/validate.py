#!/usr/bin/env python3
"""Fail-closed checks for a prim.brand kit pack."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

BLUE = re.compile(r"#6c8aff", re.I)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fail(msg: str) -> None:
    print(f"FAIL  {msg}")
    raise SystemExit(1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: validate.py <pack-dir>")
    pack = Path(sys.argv[1]).resolve()
    face = pack / "index.md"
    ident_path = pack / "identity.json"
    if not face.exists():
        fail("missing index.md")
    face_txt = face.read_text()
    if "profile: brand" not in face_txt or "type: kit" not in face_txt:
        fail("face must declare profile: brand and type: kit")
    if not ident_path.exists():
        fail("missing identity.json")
    ident = json.loads(ident_path.read_text())
    if not ident.get("logo"):
        fail("no logo assets")
    if not ident.get("typefaces"):
        fail("no typefaces")
    if not ident.get("content_blocks"):
        fail("no content_blocks")

    for logo in ident["logo"]:
        p = pack / logo["path"]
        if not p.exists():
            fail(f"missing logo {logo['path']}")
        got = sha256(p)
        if got != logo["sha256"]:
            fail(f"hash mismatch {logo['path']}: {got}")

    for tf in ident["typefaces"]:
        lic = pack / tf["license_path"]
        if not lic.exists():
            fail("missing font license")
        for f in tf["files"]:
            p = pack / f["path"]
            if not p.exists():
                fail(f"missing font {f['path']}")
            if sha256(p) != f["sha256"]:
                fail(f"hash mismatch {f['path']}")

    for block in ident["content_blocks"]:
        d = pack / block["dir"]
        for name in ("block.json", "block.html", "block.css"):
            if not (d / name).exists():
                fail(f"missing {block['dir']}/{name}")

    allowed = {pack / "identity.json", pack / "log.md"}
    for p in pack.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".svg", ".css", ".html", ".json", ".md"}:
            if p in allowed:
                continue
            if BLUE.search(p.read_text(errors="ignore")):
                fail(f"deprecated blue in {p.relative_to(pack)}")

    dtcg_path = pack / "tokens" / "dtcg.json"
    kit = pack / "kit.css"
    if dtcg_path.exists() and kit.exists():
        import re
        dtcg = json.loads(dtcg_path.read_text())
        vals = set()
        def walk(o):
            if isinstance(o, dict):
                v = o.get("$value")
                if isinstance(v, str) and v.startswith("#"):
                    vals.add(v.lower())
                for x in o.values():
                    walk(x)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(dtcg)
        for hx in set(re.findall(r"#[0-9a-fA-F]{6}", kit.read_text())):
            if hx.lower() not in vals:
                fail(f"kit.css {hx} not in tokens/dtcg.json")

    print(f"OK    {pack.name}: {len(ident['logo'])} marks, "
          f"{sum(len(t['files']) for t in ident['typefaces'])} fonts, "
          f"{len(ident['content_blocks'])} blocks")


if __name__ == "__main__":
    main()
