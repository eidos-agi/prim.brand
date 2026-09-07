"""Local DTCG 2025.10 resolution; no network or guessed CSS fallbacks."""
from __future__ import annotations
import re
from pathlib import Path
from .io import load,local
from .token_common import check,pointer,TYPES,SPACES
from .token_resolver import resolve_sets
from .token_format import resolve
from .token_types import validate_value,css_value

def compiled(pack: Path,settings: dict) -> str:
    out=['/* Generated from DTCG 2025.10; do not hand-edit. */']
    for mode,config in settings['modes'].items():
        selector=config['selector']
        check(bool(re.fullmatch(r':root|\[data-(?:palette|theme)="[a-zA-Z0-9_-]+"\]',selector)),'unsafe CSS selector')
        document=resolve_sets(pack,settings['resolver'],config['inputs']) if 'resolver' in settings else load(local(pack,settings['path']))
        tokens=resolve(document);rows=[]
        for var,name in settings['css_mapping'].items():
            check(name in tokens,f'CSS maps missing token {name}')
            t=tokens[name];rows.append(f'  {var}: {css_value(t["$type"],t["$value"])};')
        out.append(selector+' {\n'+'\n'.join(rows)+'\n}')
    return '\n'.join(out)+'\n'
