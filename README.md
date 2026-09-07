# prim.brand

A portable brand contract: identity, usable assets, tokens, lineage, and approval evidence. The pack is the record; viewers, exporters, agents and MCP adapters are replaceable operators.

## Versions

**0.2.0 is the expanded implementation candidate.** Its contract is in `SPEC.md`, its machine-readable schemas in `schemas/`, and its exact implementation boundaries in `docs/SUPPORT.md`. `brand_version` identifies the format; `identity_version` identifies the particular brand's revision.

The unchanged historical 0.1 specification is preserved in `spec/0.1.0.md`. Existing `packs/eidos`, `packs/prim`, and `scripts/validate.py` remain untouched. Their old validator continues to be available; do not mistake a historical validator pass for the new conformance report.

```sh
python3 -m pip install -r requirements-v02.txt -r requirements-export-v02.txt
python3 scripts/build_examples.py
python3 tools/brand.py schemas .
python3 -m unittest discover -s tests -v
python3 tools/brand.py validate examples/minimal
python3 tools/brand.py validate examples/comprehensive
```

## Use a pack

```sh
python3 tools/brand.py inventory PACK
python3 tools/brand.py select PACK --filters '{"id":"mark:primary"}'
python3 tools/brand.py compile PACK
python3 tools/brand.py export PACK mark:primary /tmp/brand-export --width 512
python3 tools/brand.py preview PACK /tmp/brand-inventory.html
python3 tools/brand.py release PACK /tmp/brand-release.json
python3 tools/brand.py bundle PACK /tmp/brand.prim.zip
python3 tools/brand.py diff OLD_PACK NEW_PACK
python3 tools/brand.py migrate OLD_01_PACK /tmp/migrated-pack
```

Every output destination must be new and outside its source. No command executes arbitrary pack code or fetches remote dependencies. Export receipts do not grant approval. Bundle/export tooling refuses font-file redistribution; typography can instead be referenced, system-based, or outlined.

## Small core, explicit capabilities

The core has a real YAML face, versioned identity, asset/deliverable records, rules, and a change log. Optional capabilities cover visual identity, DTCG tokens, typography dependencies, verbal identity, templates, motion, sound, localization, brand relationships, lineage, and approval records. Declaring a capability activates its requirements. A logo-only kit does not need fake fonts or web components.

The report separates **structure, integrity, completeness, brand rules, rendering evidence, and approval**. `passed`, `conformant`, and `ready_for_use` answer different questions. An internally written `approved` label is not authority. Trusted approval requires an externally maintained decision pin, bound to exact bytes and asset metadata or a release digest.

## MCP

```sh
python3 tools/mcp.py PACK --trust /protected/external-trust.json
```

The local read-only stdio adapter exposes status, inventory, exact selection, rules and validation. Pack and trust paths are operator configuration, not tool arguments. Both modern 2026-07-28 requests and legacy 2025-11-25 initialization are tested. This is not a hosted service or a claim of independent protocol certification.

## Documentation

- `SPEC.md`: normative candidate contract and source ownership.
- `docs/MIGRATION.md`: non-destructive migration and review boundaries.
- `docs/SECURITY.md`: input handling, external trust, and execution boundaries.
- `docs/SUPPORT.md`: implemented behavior and limits.
- `docs/TOOLS.md`: CLI and MCP integration.
- `docs/DELIVERY.md`: scope and acceptance gates.

Examples are synthetic and public. Private consumers, their artwork and their approval evidence must stay in their own repositories. The existing separate draft PR for the Prim product brand is not adopted by this format implementation.
