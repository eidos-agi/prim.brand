# Supported behavior and limits

| Area | Implemented | Deliberate boundary |
|---|---|---|
| Core | JSON Schema 2020-12, real face parsing, capability gates, bounded local references | No arbitrary archive ingestion |
| Assets | Hashes, SVG structure/viewBox, bitmap-wrapper rejection, bounded raster decoding/dimensions, basic PDF/font/PPTX signatures, WAV frames | Not a complete sanitizer or printer/native-platform certification |
| Tokens | DTCG 2025.10 scalar/composite records, color spaces, aliases, pointers, group inheritance, local set/modifier contexts and CSS projection | No network fetching or lossy color conversion; unsupported CSS shorthand fails explicitly |
| Typography | Bundled/reference/system/outlined strategy validation | Supplied exporters do not redistribute fonts; fallback rendering varies |
| Verbal | Positioning, tone, vocabulary, claim/evidence records | No automatic factual or legal verification |
| Templates | Slots/states/purpose, local token-consuming HTML/CSS, pinned external adapter records | External React/Figma/native implementations are not fetched or certified |
| Motion/sound | Duration and iteration limits, reduced-motion/static and silent alternatives, no autoplay, WAV duration | No production sonic logo or general animation-player certification |
| Localization/relationships | Direction, localized asset/typeface references, fallback cycle detection, version/digest/override contracts | No translation-quality certification or automatic external graph inheritance |
| Lineage/export | Source hashes, cycles, recipes, actual copy/rasterize/resize receipts and semantic diff | Other recipe operations describe provenance, not executable arbitrary code |
| Approval | Byte and metadata binding, protected external decision pins, scoped approvals and revocations | No PKI, OAuth approval UI or automatic human authentication |
| Releases | Hash snapshots, deterministic ZIP, exact verification and separate release authorization | Integrity alone is not approval |
| MCP | Read-only local stdio adapter with modern and legacy request tests | No hosted HTTP/OAuth service or independent protocol certification |

The comprehensive public example exercises all eleven capabilities. Its content and silent audio are synthetic. A capability's schema support does not imply that an independent design-tool integration has been deployed.

Validation reports recorded render evidence as recorded; it does not claim to rerun that evidence. A specific contrast ratio is not blanket accessibility certification. Actual production-artwork approval and rights clearance remain separate from passing conformance.
