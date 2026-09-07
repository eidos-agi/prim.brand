from __future__ import annotations
import copy, math, re
from .io import Invalid

TYPES={'color','dimension','fontFamily','fontWeight','duration','cubicBezier','number',
       'strokeStyle','border','transition','shadow','gradient','typography'}
SPACES={'srgb','srgb-linear','hsl','hwb','lab','lch','oklab','oklch','display-p3','a98-rgb','prophoto-rgb','rec2020','xyz-d50','xyz-d65'}
ALIAS=re.compile(r'^\{([^{}]+)\}$')
WEIGHTS={'thin','hairline','extra-light','ultra-light','light','normal','regular','book','medium','semi-bold','demi-bold','bold','extra-bold','ultra-bold','black','heavy','extra-black','ultra-black'}

def numeric(v): return type(v) in (int,float) and math.isfinite(v)
def check(ok,message):
    if not ok: raise Invalid(message)

def pointer(doc,ref):
    check(isinstance(ref,str) and (ref=='#' or ref.startswith('#/')),'only local JSON pointers are supported here')
    value=doc
    for part in ref[2:].split('/') if ref!='#' else []:
        check(not re.search(r'~(?![01])',part),'malformed JSON pointer escape')
        part=part.replace('~1','/').replace('~0','~')
        try:
            if isinstance(value,list):
                check(bool(re.fullmatch(r'0|[1-9][0-9]*',part)),'invalid array pointer index')
                value=value[int(part)]
            else: value=value[part]
        except (KeyError,IndexError,TypeError) as e: raise Invalid(f'unresolved pointer: {ref}') from e
    return value

def merge(a,b):
    if not isinstance(a,dict) or not isinstance(b,dict) or '$value' in a or '$value' in b:
        return copy.deepcopy(b)
    out=copy.deepcopy(a)
    for key,value in b.items(): out[key]=merge(out[key],value) if key in out else copy.deepcopy(value)
    return out

