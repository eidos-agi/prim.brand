# prim.brand

The **brand prim**. A kit: identity, tokens, logos, fonts, and running blocks in one sendable pack.

Its own profile (`profile: brand`). Not OKF. Successor of retired `prim.obif`.

```
prim.brand          the brand prim (this repo)
packs/eidos         first instance: Eidos AGI house kit
```

Everyday speech: “send me the brand prim.”

## Open the house kit

```bash
python3 scripts/validate.py packs/eidos
python3 -m http.server 8765 --directory packs/eidos
# open http://127.0.0.1:8765/view.html
```

`view.html` is a projection. `identity.json` is authority.

## Status

v0.1.0-draft. House kit is dogfood.

MIT — Eidos AGI. Space Grotesk: SIL OFL 1.1 (`packs/eidos/assets/fonts/OFL.txt`).
