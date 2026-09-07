# prim.brand — 0.2.0 implementation candidate

A brand prim stores a durable identity contract. It does not run an agent, own a task system, authenticate a human, or become a mandatory user interface. Normative requirements use MUST, MUST NOT, SHOULD, MAY. The JSON Schema 2020-12 documents in `schemas/` define record shapes; this document defines their semantics. Neither schema validity nor rendering quality grants approval.

## 1. Versions and core

`brand_version` MUST be `0.2.0` for this contract. It is the profile version, not a particular company's branding revision. `identity_version` is a separate semantic version for that brand. A reader MUST reject unknown required capabilities and report unknown optional capabilities. Optional extension bodies use namespaced keys. The historical 0.1 reader/specification remains available; upgrading a pack MUST be explicit and non-destructive.

The pack root contains:

```text
index.md             real YAML frontmatter and human-readable face
identity.json        identity and references; authoritative brand contract
log.md               append-only brand history
assets/              present artwork and other declared assets
```

The face MUST begin with YAML frontmatter declaring `profile: brand`, `type: kit`, `brand_version: "0.2.0"`, `title`, and `status`. Title, status and version MUST agree with `identity.json`. Matching words in a code example are not a valid face. Duplicate keys and YAML aliases are rejected by the reference implementation.

The identity MUST declare `id`, `name`, `status`, `identity_version`, `capabilities`, `required_capabilities`, `assets`, `rules`, and `deliverables`. Required capabilities MUST be a subset of capabilities. Additional arbitrary top-level fields are not permitted; extensions MUST be namespaced.

A minimal logo kit MAY declare only `visual`. It need not contain a font, CSS, or a web component. Conversely, declaring a richer capability MUST activate all of its requirements. Empty lists must not masquerade as implemented mandatory resources.

## 2. Source ownership

`identity.json` owns identity meaning, asset references, constraints, capability declarations and relationships. A referenced DTCG file owns token values. A master artwork file owns its actual geometry or pixels. A view, PNG export, PDF book, slideshow, framework adapter or MCP server MUST NOT silently replace these sources.

Each datum SHOULD have one authoritative location. Historical material MAY be retained with an explicit archival role. A historical CSS file preserved as an asset is not a second current token authority. A brand book is a projection or a referenced companion, not proof of profile conformance.

References to albums, decks, sessions, dockets or other Prim types MUST identify the external artifact and version/digest rather than copy its domain records into the identity. Brand instructions are usage data, not agent permission or an override of host policy.

## 3. Asset inventory

Every asset record MUST have a unique stable ID, role, purpose, media type, representation, availability, required flag, background treatment, editability classification, advisory approval state, and rights record.

Roles distinguish master, derivative, reference, mockup, template, export and support. Availability distinguishes present, external, planned and missing. A present asset MUST include its pack-relative path and SHA-256. External assets MUST have an HTTPS URI and expected hash; readers MUST NOT fetch them without an explicitly authorized external adapter. Planned and missing required deliverables fail completeness.

Representation distinguishes vector, raster, mixed, document, audio, video and data. Dimensions, view box, background compatibility, minimum size, clear space and allowed/forbidden transformations SHOULD be stated when relevant. A bitmap wrapped in SVG MUST NOT claim true vector geometry. Outlined lettering MUST NOT claim editable text. A picture of a slide template MUST NOT claim editable slides. Metadata describes actual files, not a preview's promises.

Rights status and redistribution permission are separate from availability. A license label is a declaration, not independent legal clearance. Evidence references SHOULD be supplied. Readers SHOULD warn when rights are unknown rather than invent ownership or permissions.

## 4. Optional capabilities

### Visual

`visual.primary_asset` MUST resolve to an asset. Usage rules describe the identity's own decisions. No particular brand palette, font, logo shape, voice or deprecated color is a universal format rule.

### Tokens

Tokens target the published **DTCG 2025.10** Format, Color and Resolver modules. The identity MUST name the token source, explicit modes, CSS mapping and CSS projection. The reference implementation supports bounded local set/modifier resolution and fails on unsupported mappings instead of silently approximating them.

Token aliases, property references and group inheritance MUST resolve without cycles. CSS variable mappings MUST name existing tokens. The generated CSS MUST match the authoritative token resolution for every declared mode. All dependency references, including nonselected resolver contexts, MUST be checked. Unsafe paths and implicit network loads are forbidden. A token's existence does not prove every platform can render it identically.

### Typography

A typeface declares one strategy:

- `bundled`: present font asset references and a present license document are required.
- `reference`: an explicit source URI and fallback stack are required; the dependency is not assumed available.
- `system`: an explicit fallback stack is required; output may vary by environment.
- `outlined`: present vector artwork is required for the fixed lettering; it is not an editable typeface.

The format can describe these strategies without requiring font redistribution. This implementation's export tools do not redistribute font binaries. Migrations report font substitution as review-required; they MUST NOT claim unchanged editable typography.

### Verbal

Positioning, tone, preferred/prohibited expressions and claim records are data. Approved claim labels require referenced evidence but MUST NOT be treated as authenticated factual or legal verification. Host tools remain responsible for publication authority and truthfulness.

### Templates

Templates declare IDs, purposes, refused uses, states, named content slots and implementation references. A declared local reference implementation uses no-build HTML/CSS consuming declared tokens. External framework/native/design-tool implementations are separately pinned adapters and MUST NOT be downloaded or executed merely by opening the pack. Preview images are distinct from editable source.

### Motion and sound

Motion records specify asset, duration, bounded iterations, purpose, and a static reduced-motion alternative. Sound records specify an audio asset, duration, purpose and a silent alternative; autoplay is false. Declaring these records does not certify arbitrary animation playback or create a production sonic signature.

### Localization and relationships

Localization names locale, writing direction, typography, copy, optional localized wordmark and fallback locale. References MUST resolve and local fallback graphs MUST be acyclic. Translation quality requires separate review.

Brand relationships identify a separate brand, version, identity digest, URI, relation kind and permitted overrides. Parent, sub-brand, endorsement, co-brand and composition relationships are supported contracts. They do not create permission to override another identity. The reference reader does not fetch or automatically inherit remote graphs.

## 5. Lineage and export recipes

Derivative/export records MUST cite source asset IDs and exact source hashes plus an existing recipe. The parent graph MUST be acyclic. Recipes describe operation, tool, version, parameters, determinism and review requirements. Reconstruction and generation MUST require review. Generative outputs MUST NOT be called deterministic merely because the same prompt can be resubmitted.

An export operation MUST preserve the original pack and respect explicit forbidden transformations. An export receipt binds source bytes, operation, tool/version, parameters and resulting file hash. A correct export can remain a candidate. Allowed-transform metadata is not a newly authenticated owner approval.

Expanding an approved identity is not permission to redesign it. Tracing raster art into new vector curves is a new candidate, not a pixel-identical original or an implicitly approved master.

## 6. Approval and external trust

Approval records live in a referenced file and contain decision ID, principal, timestamp, decision, scope, exact subjects or release digest, and hash-bound evidence. Asset subjects bind both file SHA-256 and a digest of the complete asset record excluding its advisory `approval` field. A changed geometry, usage constraint or source relationship invalidates the old binding.

Scopes are deliberately separate:

- Reference selection approves that reference only.
- Asset approval concerns exact bytes and their usage record.
- Release approval concerns the exact release snapshot.

A pack MUST NOT authorize itself. The reference implementation accepts a trust file supplied by the operator **outside** the pack, containing exact decision digests, principal and permitted scopes. Revocation and trusted reject/supersede decisions veto matching approvals. This is an out-of-band pinning model, not PKI, a digital signature scheme or automatic authentication of the named human. Protecting that trust configuration is a host responsibility.

Canonical record digests use **PBJ/1**: UTF-8 JSON, sorted object keys, no insignificant separators, unescaped Unicode and no NaN/infinity. This implementation uses Python JSON numeric serialization. It does not claim RFC 8785 JCS compatibility. Cross-language signers must reproduce these bytes or use an explicitly versioned future canonicalization format.

An advisory `approved` value without trusted evidence never satisfies readiness. Unreviewed reconstructed artwork does not inherit reference approval. Human approval, conformance, copyright/trademark clearance and deployment are distinct.

## 7. Releases and history

A release snapshot records brand identity/version and exact pack-relative file hashes. The reference snapshot excludes the approval-record file and `reports/` and `releases/` to avoid self-referential digest cycles; required artwork MUST NOT be hidden in excluded paths. Referenced substantive sources and approval evidence remain hash-covered.

A release manifest proves snapshot integrity only. Production-ready release verification additionally requires trusted release authorization and passing pack checks. Deterministic ZIP outputs have stable ordering, timestamps and attributes; binary reproducibility is asserted only where actually tested.

`log.md` is append-only by contract. Comparing two revisions MUST report whether the new log preserves the old prefix. A single isolated pack cannot prove its own historical append-only behavior. Semantic comparison MUST identify artwork and identity-rule changes and MUST NOT silently inherit approval.

## 8. Conformance reporting

Report six separate dimensions: structure, integrity, completeness, brand rules, rendering evidence, approval. Unexecuted checks MUST say `not-run`. Recorded evidence MUST say recorded, not rerun. A hash check is not proof of authorship; a dimension check is not platform certification; a contrast ratio for one pair is not blanket accessibility certification.

The reference tool uses:

- `conformant`: no structural or integrity errors.
- `passed`: no errors across the performed checks; warnings remain visible.
- `ready_for_use`: passing checks plus externally verified approvals for all required assets, with at least one required asset. Release verification has its separate release-approval gate.

Readers MUST reject malformed records, duplicate IDs, unsafe paths, missing required dependencies, stale hashes, cycles, unsupported required capabilities, and mismatched face metadata. House policy must be scoped to its pack. Conformance implementations SHOULD include adversarial tests, not just positive fixtures.

## 9. References and limits

DTCG: https://www.designtokens.org/TR/2025.10/format/ ; https://www.designtokens.org/TR/2025.10/color/ ; https://www.designtokens.org/TR/2025.10/resolver/ . JSON Schema: https://json-schema.org/draft/2020-12 . MCP adapter references: https://modelcontextprotocol.io/specification/2026-07-28/basic and https://modelcontextprotocol.io/specification/2025-11-25 . MCP is an operator contract, not part of a brand's semantic authority.

See `docs/SUPPORT.md` for the implementation's exact supported checks and boundaries. This version is an implementation candidate, not a claim of independent standards-body, security, legal, design-tool or platform certification.
