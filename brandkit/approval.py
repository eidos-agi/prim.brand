from __future__ import annotations
from pathlib import Path
import re
from .io import Invalid,load,local,sha,digest
from .schema import APPROVAL_SCHEMA,TRUST_SCHEMA
from .report import assert_schema,unique,asset_digest
from .token_common import check

def apply_rules(pack,ident,assets,r):
    for rule in ident['rules']:
        try:
            if rule['kind'] in ('forbidden-color','prohibited-term'):
                needle=rule['value'].casefold()
                for path in rule['paths']:
                    text=local(pack,path).read_text('utf-8').casefold()
                    check(needle not in text,'brand prohibition matched in '+path)
            elif rule['kind']=='asset-usage':
                check(rule['asset_id'] in assets,'unknown asset in usage rule')
                r.add('brand_rules','HUMAN_USAGE_REVIEW',rule['notes'],'warning')
            elif rule['kind']=='contrast':
                def lum(h):
                    check(bool(re.fullmatch('#[0-9a-fA-F]{6}',h)),'contrast requires explicit opaque sRGB hex pair')
                    v=[int(h[i:i+2],16)/255 for i in (1,3,5)]
                    return sum(w*(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4) for w,c in zip((.2126,.7152,.0722),v))
                a,b=sorted((lum(rule['foreground']),lum(rule['background'])))
                ratio=(b+.05)/(a+.05);check(ratio>=rule['minimum'],f'contrast {ratio:.3f} below {rule["minimum"]}')
            r.checks+=1;r.evaluated.add('brand_rules')
        except (Invalid,ValueError,OSError) as e:r.add('brand_rules',rule['id'],str(e),rule['severity'])

def verify_approvals(pack,ident,assets,trust_path,r):
    decisions=[];trusted={};revoked=set();blocked=set();verified=set()
    if 'approvals' in ident:
        def read():
            data=load(local(pack,ident['approvals']['path']));assert_schema(data,APPROVAL_SCHEMA);unique(data['decisions']);return data['decisions']
        decisions=r.run('structure','APPROVAL_RECORDS',read) or []
    if trust_path is not None:
        def trust():
            p=Path(trust_path).resolve()
            check(not p.is_relative_to(pack),'trust configuration must be outside the pack')
            data=load(p);assert_schema(data,TRUST_SCHEMA);unique(data['trusted_decisions'],'sha256');return data
        trust_data=r.run('approval','TRUST_INPUT',trust)
        if trust_data:
            trusted={t['sha256']:t for t in trust_data['trusted_decisions']};revoked=set(trust_data['revoked'])
    for d in decisions:
        try:
            check(sha(local(pack,d['evidence']['path']))==d['evidence']['sha256'],'approval evidence hash mismatch')
            pin=trusted.get(digest(d));auth=bool(pin and digest(d) not in revoked and pin['principal']==d['principal'] and d['scope'] in pin['scopes'])
            if d['scope']=='release':
                r.add('approval','RELEASE_DECISION',d['id']+': evaluated by release verification, not individual asset validation','warning');continue
            for subject in d['subjects']:
                a=assets.get(subject['asset_id'])
                check(a and a.get('sha256')==subject['sha256'] and asset_digest(a)==subject['record_sha256'],'approval subject or usage record is stale')
                if auth and d['scope']=='asset':
                    if d['decision']=='approve':verified.add(a['id'])
                    else:blocked.add(a['id'])
            if not auth:r.add('approval','UNTRUSTED_DECISION',d['id']+': not externally pinned; no approval granted','warning')
            elif d['scope']=='reference':r.add('approval','REFERENCE_ONLY',d['id']+': reference selection does not approve derivatives','warning')
        except (Invalid,OSError) as e:r.add('integrity','APPROVAL_BINDING',str(e))
    r.verified_assets=verified-blocked;r.evaluated.add('approval')
    for a in assets.values():
        if a['approval']=='approved' and a['id'] not in r.verified_assets:
            r.add('approval','SELF_ASSERTED_APPROVAL',a['id']+': approval label is unverified','warning')
    if r.required_assets-r.verified_assets:
        r.add('approval','APPROVAL_REQUIRED',f'{len(r.required_assets-r.verified_assets)} required assets lack externally verified asset approvals','warning')
