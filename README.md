# prim.brand

A **brand kit** as a Prim. Not a Brand Center. Not a CSS sheet.

You send the pack. It has identity, tokens, logos, fonts, and running blocks.
An agent who has the file can ship a house page.

```
prim.obif     identity grammar (open format)
prim.brand    the kit you send — identity plus implementations
packs/eidos   first instance: Eidos AGI house kit
```

Everyday speech: “send me the brand prim.”

## Open the house kit

```bash
python3 scripts/validate.py packs/eidos
python3 -m http.server 8765 --directory packs/eidos
# open http://127.0.0.1:8765/view.html
```

`view.html` is a projection. `identity.json` is authority.

## Pack layout

```
<kit>/
  index.md
  identity.json          # law
  tokens/dtcg.json       # DTCG 2025.10 projection
  kit.css                # CSS custom properties (view of tokens)
  assets/logos/          # hashed marks
  assets/fonts/          # hashed type + OFL
  blocks/<id>/
    block.json           # when / refuses / states
    block.html           # no-build reference
    block.css
  view.html              # specimen board
  log.md
```

## Status

v0.1.0-draft. House kit is dogfood. Retired cold blue `#6c8aff` is not in this pack.

MIT — Eidos AGI. Space Grotesk: SIL OFL 1.1 (see `packs/eidos/assets/fonts/OFL.txt`).
