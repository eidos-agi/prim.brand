# prim.brand — SPEC v0.1.0-draft

The **brand prim**. Product name: brand prim. Family name: `prim.brand`.

Its own profile. Not OKF. Not OBIF. `profile: brand`.

OBIF is retired. Do not mint `profile: obif`. Old packs are historical; there is no compatibility reader yet.

## Face

```yaml
---
profile: brand
brand_version: "0.1.0"
type: kit
title: Eidos AGI
status: active
---
```

## Store

Directory pack canonical. `identity.json` is authority.

| Path | Role |
| --- | --- |
| `index.md` | Face |
| `identity.json` | Semantic authority (foundations, logo, color, type, voice, blocks) |
| `tokens/dtcg.json` | Token interchange (DTCG) |
| `kit.css` | CSS projection of tokens |
| `assets/` | Logos, fonts, other binaries; hashes in identity.json |
| `blocks/<id>/` | `block.json` + `block.html` + `block.css` |
| `log.md` | Append-only |
| `view.html` | Optional specimen (a view) |

## Kinds

| Kind | Purpose |
| --- | --- |
| `content_block` | Named house block (Lede, PageHero, …) |
| `implementation` | In-pack HTML/CSS citing a content_block |
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

House kit extra: deprecated Eidos blue `#6c8aff` must not appear in implementations.

## Compose

A brand prim MAY compose an album, a scene, or a docket. It MUST NOT copy those files into `identity.json`.

Views (Worker, Brand Center, npm) cite this pack. They do not own tokens.

`view.html` is a projection. It is not the store.
