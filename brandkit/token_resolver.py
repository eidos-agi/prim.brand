from __future__ import annotations
import posixpath
from pathlib import Path
from .io import load, local
from .token_common import check,pointer,merge

def resolve_sets(pack: Path,path: str,inputs: dict) -> dict:
    doc=load(local(pack,path));check(isinstance(doc,dict),'resolver must be an object')
    check(isinstance(doc.get('resolutionOrder'),list) and doc['resolutionOrder'],'resolver requires resolutionOrder')
    check(not (set(doc)-{'$schema','name','description','version','sets','modifiers','resolutionOrder','$defs','extensions'}),'unknown resolver property')
    for key in ('sets','modifiers'):
        check(isinstance(doc.get(key,{}),dict),f'{key} must be an object')
    names=set(); modifiers={}; order=[]
    def deref(value,origin,document,stack):
        if not (isinstance(value,dict) and '$ref' in value): return value,origin,document
        check(set(value)=={'$ref'},'resolver reference has extra properties')
        ref=value['$ref'];check(isinstance(ref,str),'reference must be string')
        key=(origin,ref);check(key not in stack and len(stack)<64,'resolver reference cycle/limit')
        file,sep,frag=ref.partition('#')
        check(not frag.startswith('/resolutionOrder/'),'resolutionOrder items cannot be referenced')
        if file:
            check(not any(c in file for c in (':','\\','%','?')),'network/encoded resolver reference forbidden')
            target=posixpath.normpath(posixpath.join(posixpath.dirname(origin),file))
            document=load(local(pack,target));origin=target
        value=pointer(document,'#'+frag) if sep else document
        return deref(value,origin,document,stack+[key])
    for item in doc['resolutionOrder']:
        if isinstance(item,dict) and '$ref' in item:
            r=item['$ref'];check(r.startswith('#/sets/') or r.startswith('#/modifiers/'),'order ref must name a set or modifier')
            kind='modifier' if r.startswith('#/modifiers/') else 'set'
            name=r.rsplit('/',1)[1].replace('~1','/').replace('~0','~')
            entry,origin,document=deref(item,path,doc,[])
        else:
            check(isinstance(item,dict) and item.get('type') in ('set','modifier') and isinstance(item.get('name'),str),'invalid inline resolver entry')
            kind=item['type'];name=item['name'];entry=item;origin=path;document=doc
        check(name not in names,'duplicate resolutionOrder name');names.add(name)
        check(isinstance(entry,dict),'resolver entry must be object')
        if kind=='modifier':
            contexts=entry.get('contexts');check(isinstance(contexts,dict) and contexts,'modifier requires contexts')
            check(all(isinstance(v,list) for v in contexts.values()),'modifier contexts must be arrays')
            if 'default' in entry: check(entry['default'] in contexts,'unknown default context')
            modifiers[name]=entry
        else: check(isinstance(entry.get('sources'),list),'set requires sources')
        order.append((kind,name,entry,origin,document))
    check(not (set(inputs)-set(modifiers)),'unknown modifier input')
    def source(value,origin,document,stack):
        if isinstance(value,dict) and '$ref' in value:
            r=value['$ref'];check(not r.startswith('#/modifiers/'),'sets/contexts cannot reference modifiers')
            key=(origin,r);check(key not in stack and len(stack)<64,'resolver source cycle/limit')
            resolved,new_origin,new_doc=deref(value,origin,document,[])
            return source(resolved,new_origin,new_doc,stack+[key])
        check(isinstance(value,dict),'source must be tokens or reference')
        if 'sources' in value and '$value' not in value:
            check(isinstance(value['sources'],list),'sources must be array')
            result={}
            for v in value['sources']: result=merge(result,source(v,origin,document,stack))
            return result
        check('contexts' not in value,'modifier used as source')
        return value
    # Check dependencies in *all* contexts, not just the chosen one.
    for kind,name,entry,origin,document in order:
        lists=entry['contexts'].values() if kind=='modifier' else [entry['sources']]
        for values in lists:
            for value in values: source(value,origin,document,[])
    result={}
    for kind,name,entry,origin,document in order:
        if kind=='modifier':
            selected=inputs.get(name,entry.get('default'))
            check(selected in entry['contexts'],f'missing/invalid context for {name}')
            sources=entry['contexts'][selected]
        else: sources=entry['sources']
        for value in sources: result=merge(result,source(value,origin,document,[]))
    return result

