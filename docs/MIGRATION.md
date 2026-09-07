# Migration and compatibility

Existing 0.1 packs remain readable by the unchanged `scripts/validate.py`; their specification is archived at `spec/0.1.0.md`. The 0.2 reader does not guess a version from filenames or reinterpret a brand's revision number as a profile version.

Run `python3 tools/brand.py migrate OLD_PACK NEW_DIRECTORY`. The destination must not exist and must be outside the source. The source face must explicitly declare version 0.1.0 and its identity must agree. Migration checks existing logo hashes and preserves their bytes. It never redesigns artwork or inherits approval.

The result archives the entire legacy identity and, when present, the original tokens. Old `$schema` metadata is retained in that archive rather than misread as a design token. Legacy hex colors and dimension/duration strings are converted to structured DTCG 2025.10 values, including inherited token types. A new explicit CSS mapping is generated and marked for review.

Bundled font binaries are not redistributed by this implementation. Their family names become explicit system-fallback declarations, with review-required notes. This preserves information about intended typography but does not promise exact editable reproduction.

Legacy blocks are preserved as migration metadata, not silently recast as tested new components. Their HTML/CSS should be deliberately adapted to the new token contract and checked before claiming the templates capability. Original legacy files remain untouched.

The migration result must pass the 0.2 validator before the destination is published. `migration-report.json` lists substitutions, preserved data and review requirements. Unsupported conversion fails instead of guessing.

The CI suite validates both unchanged real house packs with their legacy validator, migrates each in a temporary directory, validates the results and compares every original file hash. A format upgrade can be implemented without silently adopting a new corporate/product brand or merging the separate brand-design PR.
