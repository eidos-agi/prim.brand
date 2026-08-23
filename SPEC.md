# prim.brand — SPEC v0.1.0-draft

Profile for a **brand kit** Prim. Product name: brand prim. Family name: `prim.brand`.

Additive of [OBIF](https://github.com/eidos-agi/prim.obif) identity domains. Not a replacement of the identity grammar.

## Face

```yaml
---
profile: brand
brand_version: "0.1.0"
okf_version: "0.2"
obif_version: "0.1.0"
type: kit
title: Eidos AGI
status: active
---
```

## Store

Directory pack canonical.

| Path | Role |
| --- | --- |
| `index.md` | Face |
| `identity.json` | Semantic authority |
| `tokens/dtcg.json` | Token interchange (DTCG) |
| `kit.css` | CSS projection of tokens |
| `assets/` | Logos, fonts, other binaries + hashes in identity.json |
| `blocks/<id>/` | `block.json` + `block.html` + `block.css` |
| `log.md` | Append-only |
| `view.html` | Optional specimen projection |

## Kinds

OBIF kinds plus:

| Kind | Purpose |
| --- | --- |
| `content_block` | Named house block (Lede, PageHero, …) |
| `implementation` | In-pack HTML/CSS (or later Swift) citing a content_block |
| `token_mode` | paper / ink / system |

`content_block` fields: `id`, `name`, `when`, `refuses[]`, `states[]`, `implementation`.

An implementation MUST be no-build HTML+CSS that consumes `kit.css` tokens only. No framework in the pack.

## Gates

| Rule | Level |
| --- | --- |
| Face `profile: brand` + `type: kit` | error |
| `identity.json` present | error |
| At least one logo asset with hash | error |
| At least one in-pack font with hash + license | error |
| Every `content_block` has `block.html` + `block.css` on disk | error |
| Tokens used in CSS exist in `tokens/dtcg.json` | error |
| Deprecated Eidos blue `#6c8aff` must not appear | error (house kit) |

## Compose

A brand kit MAY be read as OBIF for identity-only tools. Extra keys (`content_block`, `implementation`) are ignored by identity-only renderers.

Views (Worker, Brand Center, npm) cite this pack. They do not own tokens.
