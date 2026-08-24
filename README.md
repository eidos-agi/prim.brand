# prim.brand

The **brand prim**. A kit: identity, tokens, logos, fonts, and running blocks in one sendable pack.

Its own profile (`profile: brand`). Not OKF. Successor of retired `prim.obif`.

```
prim.brand          the brand prim (this repo)
packs/eidos         Eidos AGI house kit (company)
packs/prim          Prim product/category kit (prims.sh and Prim-facing UIs)
```

Everyday speech: “send me the brand prim.”

## Open a kit

```bash
python3 scripts/validate.py packs/eidos
python3 scripts/validate.py packs/prim
python3 -m http.server 8765 --directory packs/prim
# open http://127.0.0.1:8765/view.html
```

Consumers link `packs/prim/kit.css` (or `packs/eidos/kit.css`). Set `data-palette` to `ink`, `paper`, or `system`. Do not copy tokens out of the pack.

`view.html` is a projection. `identity.json` is authority.

## Status

v0.1.0-draft. House kit is dogfood.

MIT — Eidos AGI. Space Grotesk: SIL OFL 1.1 (`packs/eidos/assets/fonts/OFL.txt`). Instrument Sans + IBM Plex Mono: SIL OFL 1.1 (`packs/prim/assets/fonts/OFL.txt`).
