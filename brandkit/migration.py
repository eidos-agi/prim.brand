"""Explicit, non-destructive 0.1-to-0.2 migration with review notes."""
from __future__ import annotations
from pathlib import Path
import copy,json,mimetypes,re,shutil,tempfile
from .io import Invalid,load,local,face,sha,digest,save,files,output_root
from .tokens import compiled,resolve,check
from .validate import validate,assert_schema
from .schema import SCHEMA

def migrate(source: Path,target: Path):
    """Non-destructive v0.1 reader/migrator. Never promotes approvals or copies fonts."""
    from .operations import compile_tokens,FONT_SUFFIXES
    source=Path(source).resolve();target=output_root(source,target);old_face=face(source)
    check(old_face.get('brand_version')=='0.1.0','explicit v0.1.0 source required; pack revision is not profile version')
    old=load(local(source,'identity.json'));check(old.get('brand_version')=='0.1.0','legacy identity version mismatch')
    unique_ids=set();assets=[];notes=[];copies=[]
    for a in old.get('logo',[]):
        check(a['id'] not in unique_ids,'duplicate legacy logo ID');unique_ids.add(a['id'])
        p=local(source,a['path']);check(sha(p)==a['sha256'],'legacy logo hash mismatch')
        check(p.suffix.lower() not in FONT_SUFFIXES,'logo cannot be a font')
        copies.append(a['path']);mime=mimetypes.guess_type(a['path'])[0] or 'application/octet-stream'
        assets.append({'id':a['id'],'role':'master','purpose':a.get('role','logo'),'media_type':mime,
          'representation':'vector' if mime=='image/svg+xml' else 'raster','availability':'present','required':True,
          'path':a['path'],'sha256':a['sha256'],'background':'unknown','editable':'geometry' if mime=='image/svg+xml' else 'none',
          'approval':'unreviewed','rights':{'status':'unknown','redistribution':'unknown'}})
    check(assets,'legacy kit has no logo assets')
    typography=[]
    for tf in old.get('typefaces',[]):
        typography.append({'id':tf['id'],'family':tf['family'],'strategy':'system','roles':tf.get('roles',['body']),
          'fallbacks':[tf['family'],'sans-serif'],'notes':'Legacy font binaries not copied. This is a fallback declaration, not exact typography reproduction.'})
        notes.append({'kind':'typography','id':tf['id'],'action':'system-fallback','review_required':True})
    brand=old.get('brand',{});identity={'profile':'brand','brand_version':'0.2.0','identity_version':'1.0.0-migrated',
      'id':brand.get('id','brand:migrated'),'name':brand.get('display_name',old_face.get('title','Migrated brand')),
      'status':'draft','capabilities':['visual'],'required_capabilities':['visual'],'assets':assets,'rules':[],
      'deliverables':[{'id':'deliverable:primary','asset_id':assets[0]['id'],'required':True,'purpose':'Primary legacy mark'}],
      'visual':{'primary_asset':assets[0]['id'],'usage':old.get('usage_rules',[])}}
    if typography:identity['typography']=typography;identity['capabilities'].append('typography')
    if old.get('voice'):
        v=old['voice'];identity['capabilities'].append('verbal');identity['verbal']={'positioning':brand.get('positioning','Legacy identity; review positioning.'),'tone':v.get('attributes') or ['As documented in source'],'preferred':v.get('do',[]),'prohibited':v.get('dont',[]),'claims':[]}
    # Keep legacy content metadata for explicit review, never silently reinterpret it.
    identity['extensions']={'org.prims.legacy':{'profile_version':'0.1.0','identity_sha256':sha(local(source,'identity.json')),
        'blocks':old.get('content_blocks',[]),'deprecated':old.get('deprecated',{})}}
    for block in old.get('content_blocks',[]):notes.append({'kind':'block','id':block['id'],'action':'preserved-as-migration-reference','review_required':True})
    legacy_tokens=None;raw_legacy_tokens=None
    if (source/'tokens/dtcg.json').exists():
        raw_legacy_tokens=load(local(source,'tokens/dtcg.json'))
        legacy_tokens=copy.deepcopy(raw_legacy_tokens)
        legacy_tokens.pop('$schema',None)
        def convert(node,inherited=None):
            if isinstance(node,dict):
                typ=node.get('$type',inherited)
                out={k:convert(v,typ) if not k.startswith('$') else copy.deepcopy(v) for k,v in node.items()}
                v=out.get('$value')
                if typ=='color' and isinstance(v,str) and re.fullmatch('#[0-9a-fA-F]{6}',v):out['$value']={'colorSpace':'srgb','components':[int(v[i:i+2],16)/255 for i in (1,3,5)]}
                if typ in ('dimension','duration') and isinstance(v,str):
                    m=re.fullmatch(r'(-?[0-9.]+)(px|rem|ms|s)',v)
                    if m:out['$value']={'value':float(m.group(1)),'unit':m.group(2)}
                return out
            if isinstance(node,list):return [convert(x,inherited) for x in node]
            return node
        legacy_tokens=convert(legacy_tokens);resolved=resolve(legacy_tokens)
        mapping={}
        for name,t in resolved.items():
            var='--brand-'+re.sub('[^a-zA-Z0-9_-]','-',name)
            check(var not in mapping,'legacy CSS-name collision')
            if t['$type']!='typography':mapping[var]=name
        identity['capabilities'].append('tokens');identity['tokens']={'version':'2025.10','path':'tokens/dtcg.json',
          'modes':{'default':{'inputs':{},'selector':':root'}},'css':'kit.css','css_mapping':mapping}
        notes.append({'kind':'tokens','action':'converted-values-and-new-CSS-map','review_required':True})
    assert_schema(identity,SCHEMA)
    notes.append({'kind':'source','action':'archive-full-legacy-identity-as-data','review_required':False})
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temp:
        work=Path(temp)/'pack';work.mkdir()
        for path in copies:
            dest=work/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(local(source,path),dest)
        save(work/'identity.json',identity)
        save(work/'migration/legacy-identity.json',old)
        if raw_legacy_tokens is not None:save(work/'migration/legacy-tokens.json',raw_legacy_tokens)
        (work/'index.md').write_text('---\nprofile: brand\ntype: kit\nbrand_version: "0.2.0"\ntitle: '+json.dumps(identity['name'])+'\nstatus: draft\n---\n\nMigrated identity; review the migration report.\n','utf-8')
        (work/'log.md').write_text('# Change log\n\nMigrated non-destructively from a v0.1.0 pack. No approval inherited.\n','utf-8')
        if legacy_tokens is not None:save(work/'tokens/dtcg.json',legacy_tokens);compile_tokens(work)
        save(work/'migration-report.json',{'source_identity_sha256':sha(local(source,'identity.json')),'actions':notes,'approval_inherited':False,'fonts_redistributed':False})
        report=validate(work);check(report['passed'],'migration result failed validation: '+json.dumps(report['findings']))
        shutil.move(str(work),str(target))
    return {'destination':str(target),'report':validate(target),'actions':notes}
