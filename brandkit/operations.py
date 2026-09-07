"""Replaceable tools: compile, select, migrate, compare, release, and inert preview."""
from __future__ import annotations
from pathlib import Path
import copy
import html
import json
import mimetypes
import re
import shutil
import tempfile
import zipfile
from .io import Invalid, load, local, face, sha, digest, save, files, output_root
from .tokens import compiled, resolve, check
from .validate import validate, asset_digest, assert_schema
from .schema import SCHEMA, TRUST_SCHEMA, APPROVAL_SCHEMA

FONT_SUFFIXES={'.ttf','.otf','.woff','.woff2','.ttc'}

def compile_tokens(pack: Path):
    pack=Path(pack).resolve();ident=load(local(pack,'identity.json'));assert_schema(ident,SCHEMA)
    settings=ident.get('tokens');check(settings is not None,'pack has no tokens capability')
    text=compiled(pack,settings);p=local(pack,settings['css'],False);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,'utf-8')
    return {'path':settings['css'],'sha256':sha(p)}

def inventory(pack: Path,filters: dict|None=None,trust: Path|None=None):
    pack=Path(pack).resolve();report=validate(pack,trust);check(report['conformant'],'invalid pack; run validate')
    ident=load(local(pack,'identity.json'));filters=filters or {}
    check(not(set(filters)-{'id','role','purpose','background','media_type','width','height','approved'}),'unknown asset filter')
    out=[]
    for a in ident['assets']:
        if a['availability']!='present':continue
        if filters.get('approved') and a['id'] not in report['verified_assets']:continue
        if any(a.get(k)!=v for k,v in filters.items() if k!='approved'):continue
        out.append({**a,'verified_approval':a['id'] in report['verified_assets']})
    return out

def select(pack: Path,filters: dict,trust: Path|None=None):
    result=inventory(pack,filters,trust)
    check(len(result)==1,f'asset selection is {"empty" if not result else "ambiguous"}; matched {len(result)}')
    return result[0]

def snapshot(pack: Path):
    pack=Path(pack).resolve();ident=load(local(pack,'identity.json'))
    excluded={ident.get('approvals',{}).get('path','approvals.json')}
    names=[p for p in files(pack) if p not in excluded and not p.startswith(('reports/','releases/'))]
    # Hash-covered source dependencies must not be hidden in excluded report/release paths.
    for a in ident['assets']:
        if a['availability']=='present':check(a['path'] in names,'asset placed in non-release directory')
    return {'profile':'brand-release','version':'0.2.0','brand_id':ident['id'],'identity_version':ident['identity_version'],
            'files':[{'path':p,'sha256':sha(local(pack,p))} for p in names]}

def release(pack: Path,target: Path):
    pack=Path(pack).resolve();report=validate(pack);check(report['passed'],'pack has failing checks; cannot release')
    target=output_root(pack,target)
    value=snapshot(pack);value['sha256']=digest(value);save(target,value)
    return value

def verify_release(pack: Path,path: Path,trust: Path|None=None):
    report=validate(pack,trust);published=load(Path(path));current=snapshot(pack)
    match=published.get('sha256')==digest(current) and {k:v for k,v in published.items() if k!='sha256'}==current
    authorized=False
    if trust is not None:
        tp=Path(trust).resolve();check(not tp.is_relative_to(Path(pack).resolve()),'trust must be external')
        t=load(tp);assert_schema(t,TRUST_SCHEMA)
        pins={x['sha256']:x for x in t['trusted_decisions']};revoked=set(t['revoked'])
        ident=load(local(Path(pack),'identity.json'))
        if 'approvals' in ident:
            approvals=load(local(Path(pack),ident['approvals']['path']));assert_schema(approvals,APPROVAL_SCHEMA)
            accepted=False;veto=False
            for d in approvals['decisions']:
                p=pins.get(digest(d))
                if p and digest(d) not in revoked and p['principal']==d['principal'] and d['scope']=='release' and 'release' in p['scopes'] and d['release_sha256']==published.get('sha256'):
                    check(sha(local(Path(pack),d['evidence']['path']))==d['evidence']['sha256'],'release decision evidence mismatch')
                    if d['decision']=='approve':accepted=True
                    else:veto=True
            authorized=accepted and not veto
    return {'integrity_matches':match,'authorized':authorized,'ready_for_use':match and authorized and report['passed'], 'validation':report}

def bundle(pack: Path,target: Path):
    pack=Path(pack).resolve();check(validate(pack)['passed'],'pack has failing checks')
    target=output_root(pack,target);names=files(pack)
    for name in names:
        check(Path(name).suffix.lower() not in FONT_SUFFIXES,'this exporter does not redistribute font files; use referenced/system/outlined strategies')
        check(not any(part in {'.git','.env','secrets','id_rsa'} for part in Path(name).parts),'sensitive/administrative file in pack')
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name in names:
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,local(pack,name).read_bytes())
    return {'sha256':sha(target),'files':len(names),'path':str(target)}

def diff(before: Path,after: Path):
    a=load(local(Path(before),'identity.json'));b=load(local(Path(after),'identity.json'))
    assert_schema(a,SCHEMA);assert_schema(b,SCHEMA)
    aa={x['id']:x for x in a['assets']};bb={x['id']:x for x in b['assets']};changes=[]
    for key in sorted(aa.keys()|bb.keys()):
        if key not in aa:kind='asset-added'
        elif key not in bb:kind='asset-removed'
        elif aa[key].get('sha256')!=bb[key].get('sha256'):kind='artwork-changed'
        elif asset_digest(aa[key])!=asset_digest(bb[key]):kind='usage-or-metadata-changed'
        else:continue
        changes.append({'id':key,'change':kind,'review_required':True})
    for key in ('name','visual','verbal','typography','tokens','rules','localization','relationships'):
        changed=a.get(key)!=b.get(key)
        if key=='tokens' and a.get(key) and b.get(key):
            changed=changed or compiled(Path(before),a[key])!=compiled(Path(after),b[key])
        if changed:changes.append({'id':key,'change':'identity-contract-changed','review_required':True})
    old_log=local(Path(before),'log.md').read_bytes();new_log=local(Path(after),'log.md').read_bytes()
    return {'same_brand':a['id']==b['id'],'changes':changes,'approval_inherited':False,'log_append_only':new_log.startswith(old_log)}

def preview(pack: Path,target: Path):
    """An inert inventory document: no pack HTML, SVG, JS or remote resources execute."""
    pack=Path(pack).resolve();report=validate(pack);check(report['conformant'],'invalid pack')
    ident=load(local(pack,'identity.json'));target=output_root(pack,target)
    e=html.escape;rows=[]
    for a in ident['assets']:
        rows.append('<tr>'+''.join('<td>'+e(str(a.get(k,'')))+'</td>' for k in ('id','purpose','role','availability','media_type','background','approval'))+'</tr>')
    doc='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'"><title>'+e(ident['name'])+' — asset inventory</title><style>body{font:16px/1.5 system-ui;margin:3rem;max-width:100%}table{border-collapse:collapse;width:100%}td,th{text-align:left;vertical-align:top;padding:.7rem;border-bottom:1px solid #ccc;overflow-wrap:anywhere}.scroll{overflow:auto}h1{font-size:2rem}small{color:#444}</style><h1>'+e(ident['name'])+'</h1><p>Identity '+e(ident['identity_version'])+' · profile '+e(ident['brand_version'])+'</p><p>This is a generated inventory, not an approval record. Source artwork is not executed in this view.</p><div class="scroll"><table><thead><tr>'+''.join('<th>'+x+'</th>' for x in ('ID','Purpose','Role','Availability','Media type','Background','Advisory status'))+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></html>'
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(doc,'utf-8');return {'path':str(target),'assets':len(rows)}

from .migration import migrate
