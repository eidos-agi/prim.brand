from __future__ import annotations
import copy
from .io import Invalid
from .token_common import check,pointer,merge,ALIAS,TYPES
from .token_types import validate_value

def resolve(document: dict) -> dict:
    check(isinstance(document,dict),'tokens must be an object')
    original=copy.deepcopy(document)
    def expand(group,path,stack):
        check(isinstance(group,dict),'group must be object')
        key='.'.join(path)
        check(key not in stack and len(stack)<64,'group inheritance cycle/limit')
        out=copy.deepcopy(group)
        if '$extends' in group:
            reference=group['$extends']
            if isinstance(reference,str) and ALIAS.fullmatch(reference):
                parts=ALIAS.fullmatch(reference).group(1).split('.')
                target=original
                try:
                    for p in parts: target=target[p]
                except (KeyError,TypeError) as e: raise Invalid('unresolved group extension') from e
            else:
                r=reference.get('$ref') if isinstance(reference,dict) else reference
                target=pointer(original,r);parts=tuple(r[2:].split('/'))
            check(isinstance(target,dict) and '$value' not in target,'group extends non-group')
            inherited=expand(target,tuple(parts),stack+[key])
            out.pop('$extends');out=merge(inherited,out)
        for k,v in list(out.items()):
            if not k.startswith('$') and isinstance(v,dict) and '$value' not in v:
                out[k]=expand(v,path+(k,),stack+[key])
        return out
    document=expand(original,(),[]); tokens={}
    def walk(group,prefix=(),inherited=None):
        check(not ('$value' in group),'root/group cannot contain a value and children')
        inherited=group.get('$type',inherited)
        if '$description' in group:check(isinstance(group['$description'],str),'group description must be string')
        if '$extensions' in group:check(isinstance(group['$extensions'],dict),'group extensions must be object')
        if '$deprecated' in group:check(isinstance(group['$deprecated'],(str,bool)),'invalid group deprecation')
        if inherited is not None: check(inherited in TYPES,'unknown inherited token type')
        for key,node in group.items():
            if key.startswith('$'):
                check(key in ('$type','$description','$extensions','$deprecated','$root'),'unknown reserved group property')
                if key!='$root': continue
            else: check(not any(c in key for c in '{}.'),'forbidden token-name character')
            check(isinstance(node,dict),'tokens/groups must be objects')
            p=prefix+(key,)
            if '$value' in node:
                check(not (set(node)-{'$value','$type','$description','$extensions','$deprecated'}),'token has unknown fields or children')
                if '$description' in node: check(isinstance(node['$description'],str),'description must be string')
                if '$extensions' in node: check(isinstance(node['$extensions'],dict),'extensions must be object')
                if '$deprecated' in node: check(isinstance(node['$deprecated'],(str,bool)),'invalid deprecation')
                tokens['.'.join(p)]=(node,node.get('$type',inherited))
            else:
                check(key!='$root','$root must be a token')
                walk(node,p,inherited)
    walk(document);check(tokens,'token document has no tokens');done={}
    def value(v,stack):
        if isinstance(v,str) and ALIAS.fullmatch(v): return token(ALIAS.fullmatch(v).group(1),stack)['$value']
        if isinstance(v,dict):
            if '$ref' in v:
                check(set(v)=={'$ref'},'pointer reference has extra properties')
                r=v['$ref']; key='pointer:'+str(r)
                check(key not in stack and len(stack)<128,'pointer cycle/limit')
                return value(pointer(document,r),stack+[key])
            return {k:value(x,stack) for k,x in v.items()}
        if isinstance(v,list): return [value(x,stack) for x in v]
        return v
    def token(name,stack):
        key='token:'+name;check(key not in stack and len(stack)<128,'token alias cycle/limit')
        if name in done:return done[name]
        check(name in tokens,f'unresolved token: {name}')
        node,kind=tokens[name];raw=node['$value']
        if isinstance(raw,str) and ALIAS.fullmatch(raw):
            other=token(ALIAS.fullmatch(raw).group(1),stack+[key])
            if kind: check(kind==other['$type'],'alias type mismatch')
            kind=kind or other['$type']
        check(kind in TYPES,f'missing/unsupported type: {name}')
        v=value(raw,stack+[key]);validate_value(kind,v)
        done[name]={'$type':kind,'$value':v};return done[name]
    for name in tokens: token(name,[])
    return done

