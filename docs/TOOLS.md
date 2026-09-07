# CLI and adapters

Install `requirements-v02.txt`; add `requirements-export-v02.txt` for raster export. Run `python3 tools/brand.py --help`. Commands return JSON and nonzero status on failure.

```sh
python3 tools/brand.py validate PACK
python3 tools/brand.py inventory PACK --filters '{"background":"dark"}'
python3 tools/brand.py select PACK --filters '{"id":"mark:primary"}'
python3 tools/brand.py compile PACK
python3 tools/brand.py export PACK mark:primary /tmp/export --width 512
python3 tools/brand.py release PACK /tmp/release.json
python3 tools/brand.py verify-release PACK /tmp/release.json --trust /protected/trust.json
python3 tools/brand.py bundle PACK /tmp/brand.prim.zip
python3 tools/brand.py diff OLD NEW
python3 tools/brand.py preview PACK /tmp/inventory.html
python3 tools/brand.py migrate OLD /tmp/new-brand
```

Selection returns exactly one match or fails. `--filters '{"approved":true}'` requires externally verified approval through `--trust`, not the asset's advisory label. Inventory is a list, not an implicit choice. Outputs must be new and outside the source; compile writes only the declared CSS projection. Exports preserve the source, respect explicit prohibitions, and include receipts without minting approval.

## Read-only MCP

Run `python3 tools/mcp.py PACK [--trust /protected/trust.json]`. Configure the interpreter, script, pack and optional trust path in the client. No secrets belong in the pack.

Tools: `brand_status`, `brand_assets` (paginated), `brand_select`, `brand_rules`, `brand_validate`. There are no write, approve, execute or arbitrary-file-read tools. Pack and trust are startup configuration, never model-supplied paths.

The adapter supports tested local stdio requests using 2026-07-28 per-request metadata and discovery, plus the 2025-11-25 initialization compatibility path. Host/client installation and hosted HTTP/OAuth are separate deployment concerns. The test suite includes a real stdio subprocess, not merely mocked methods. Independent certification is not claimed.

A production consumer should cite an immutable release digest and asset record rather than a mutable branch name. Render at its real dimensions/background/language, and record that evidence separately from owner approval. Brand tone does not override agent safety or permissions. The viewer/exporter/model can be replaced without moving the identity source of truth.
