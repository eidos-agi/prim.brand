# Security and trust boundaries

The identity is data, not code authority. Opening or validating a brand must not execute an agent, grant publication rights, start a server, read arbitrary files or fetch remote dependencies. External reference records are reported, not fetched.

The local reader rejects duplicate JSON/YAML keys, YAML aliases, non-finite JSON numbers, unsafe/encoded/absolute paths, traversal and symlink components. It limits JSON size/depth/node count, face length, asset size and file count. Source directories should still be immutable or otherwise protected against concurrent file replacement; this is not an OS sandbox.

SVG inspection uses DefusedXML, rejects active elements, event handlers, external dependencies and falsely claimed vector wrappers. Raster decoding is bounded. PDF signature and PPTX container checks are intentionally not full sanitizers. Reference HTML is restricted; the generated inventory escapes text and does not execute source HTML/SVG or load remote assets. Do not present inspection as comprehensive malware or browser-safety certification.

Approval authority is external to the pack. A protected operator-supplied trust file pins exact decision digests, principals and scopes. The pack cannot supply its own trust root. This model does not authenticate a human merely from their name, and does not implement PKI. Revocations and negative decisions take precedence. A reference approval does not approve derived geometry.

The local MCP server has no network listener, mutable tool, arbitrary-path read, approval write or publication operation. Its pack/trust paths are fixed by the operator at startup. Host agent permissions and safety policy remain independent of brand voice and instructions.

Export tools use pinned libraries, bounded output sizes and new destinations outside source packs. They never run arbitrary recipes. Explicit forbidden transformations are rejected. A generated file remains a candidate unless independently authorized.

The supplied distribution tools refuse font binaries. Legacy font-bearing packs stay in their existing repository unchanged. Migration emits declared fallback strategies with review notes, not a claim of identical typography.

Run tests and conformance checks on every revision. Review exact source changes and consumer evidence before adopting a new profile or production identity. Formal penetration testing, native platform certification, trademark clearance and authenticated approval UI are separate gates.
