"""Multidimensional validation; ownership and approval remain independent."""
from __future__ import annotations
from pathlib import Path
import wave
from .io import face,load,local,files,sha
from .schema import SCHEMA,CAPABILITIES
from .report import Report,schema_errors,assert_schema,unique,asset_digest,graph
from .asset_checks import inspect_asset,SafeHTML,css_scan
from .approval import apply_rules,verify_approvals
from .tokens import compiled,check

def validate(pack: Path,trust_path: Path|None=None):
    pack=Path(pack).resolve();r=Report()
    f=r.run('structure','FACE',lambda:face(pack),'index.md')
    ident=r.run('structure','IDENTITY',lambda:load(local(pack,'identity.json')),'identity.json')
    if not isinstance(ident,dict):return r.finish()
    r.identity=ident
    errors=schema_errors(ident,SCHEMA)
    for e in errors:r.add('structure','SCHEMA',e.message,path='/'+('/'.join(map(str,e.path))))
    if f:
        r.run('structure','FACE_MATCH',lambda:check(f.get('brand_version')==ident.get('brand_version') and f.get('title')==ident.get('name') and f.get('status')==ident.get('status'),'face/version/title/status mismatch'))
    if errors:return r.finish()
    r.run('integrity','PACK_BOUNDARY',lambda:files(pack))
    r.run('structure','LOG',lambda:local(pack,'log.md'))
    caps=set(ident['capabilities']);required=set(ident['required_capabilities'])
    r.run('structure','CAPABILITY_SUBSET',lambda:check(required<=caps,'required capabilities not declared'))
    for c in caps-set(CAPABILITIES):
        if c in required:r.add('structure','UNSUPPORTED_REQUIRED_CAPABILITY',c)
        else:r.add('structure','UNSUPPORTED_OPTIONAL_CAPABILITY',c,'warning')
        r.run('structure','EXTENSION_BODY',lambda c=c:check(c in ident.get('extensions',{}),'unknown capability requires namespaced extension body'))
    for key in ('assets','recipes','typography','templates','motion','sound','relationships','rules','deliverables','evidence'):
        r.run('structure','UNIQUE_ID',lambda key=key:unique(ident.get(key,[])),key)
    assets={a['id']:a for a in ident['assets']};recipes={x['id']:x for x in ident.get('recipes',[])}
    r.required_assets={a['id'] for a in assets.values() if a['required']}
    r.required_assets|={d['asset_id'] for d in ident['deliverables'] if d['required']}
    for a in assets.values():
        r.evaluated.add('completeness')
        if a['availability']=='present':r.run('integrity','ASSET',lambda a=a:inspect_asset(pack,a),a['path'])
        else:r.add('completeness','ASSET_'+a['availability'].upper(),a['id'],'error' if a['id'] in r.required_assets else 'warning')
        if a['rights']['status']!='declared':r.add('completeness','RIGHTS_UNVERIFIED',a['id']+': rights not independently established','warning')
        if 'evidence' in a['rights']:r.run('integrity','RIGHTS_REFERENCE',lambda a=a:local(pack,a['rights']['evidence']))
        for source in a.get('derived_from',[]):
            r.run('integrity','LINEAGE_SOURCE',lambda source=source:check(source['id'] in assets and assets[source['id']].get('sha256')==source['sha256'],'missing or stale lineage source'))
        if 'recipe' in a:
            r.run('structure','RECIPE_REFERENCE',lambda a=a:check(a['recipe'] in recipes,'unknown recipe'))
    r.run('integrity','LINEAGE_GRAPH',lambda:graph({a['id']:[s['id'] for s in a.get('derived_from',[])] for a in assets.values()},'lineage'))
    for rec in recipes.values():
        if rec['operation'] in ('reconstruct','generate'):
            r.run('brand_rules','NEW_DESIGN_REVIEW',lambda rec=rec:check(rec['requires_review'],'reconstruction/generation must require review'))
        if rec['operation']=='generate':r.run('structure','GENERATION_REPEATABILITY',lambda rec=rec:check(not rec['deterministic'],'generative recipe cannot assert deterministic output'))
    def asset_ref(asset_id):check(asset_id in assets,f'unresolved asset: {asset_id}');return assets[asset_id]
    for d in ident['deliverables']:r.run('integrity','DELIVERABLE_REFERENCE',lambda d=d:asset_ref(d['asset_id']))
    if 'visual' in caps:
        r.run('integrity','PRIMARY_ASSET',lambda:asset_ref(ident['visual']['primary_asset']))
    for tf in ident.get('typography',[]):
        for aid in tf.get('asset_ids',[]):r.run('integrity','TYPEFACE_REFERENCE',lambda aid=aid:asset_ref(aid))
        if tf['strategy']=='bundled':
            r.run('integrity','FONT_LICENSE',lambda tf=tf:local(pack,tf['license_path']))
            for aid in tf['asset_ids']:
                r.run('integrity','FONT_DEPENDENCY',lambda aid=aid:check(asset_ref(aid)['media_type'].startswith('font/') and asset_ref(aid)['availability']=='present','bundled font missing/wrong type'))
        if tf['strategy']=='outlined':
            for aid in tf['asset_ids']:r.run('integrity','OUTLINED_DEPENDENCY',lambda aid=aid:check(asset_ref(aid)['representation']=='vector' and asset_ref(aid)['availability']=='present','outlined asset must be present vector'))
        if tf['strategy'] in ('reference','system'):r.add('completeness','TYPOGRAPHY_DEPENDENCY',tf['family']+': '+tf['strategy']+'; typography may differ by environment','warning')
    settings=ident.get('tokens');variables=set(settings['css_mapping']) if settings else set()
    if settings:
        r.run('integrity','TOKEN_FILE',lambda:local(pack,settings['path']))
        expected=r.run('integrity','DTCG',lambda:compiled(pack,settings))
        if expected is not None:r.run('integrity','CSS_PROJECTION',lambda:check(local(pack,settings['css']).read_text('utf-8')==expected,'CSS differs from authoritative tokens; run compile'))
    for block in ident.get('templates',[]):
        implementation=block['implementation'];r.run('structure','SLOT_IDS',lambda block=block:unique(block['slots'],'name'))
        if implementation['kind']=='external':
            r.add('completeness','EXTERNAL_IMPLEMENTATION',block['id']+': not fetched or executed','warning');continue
        def validate_block(block=block,impl=implementation):
            check(settings is not None,'HTML/CSS block requires tokens capability')
            parser=SafeHTML();p=local(pack,impl['html']);parser.feed(p.read_text('utf-8'));parser.close()
            for u in parser.urls:
                if u.startswith('#'):continue
                normalized=__import__('posixpath').normpath(str(Path(impl['html']).parent/u))
                local(pack,normalized)
            css=local(pack,impl['css']).read_text('utf-8');css_scan(css,variables,True)
        r.run('integrity','REFERENCE_BLOCK',validate_block)
        if 'preview_asset' in block:r.run('integrity','PREVIEW_REFERENCE',lambda block=block:asset_ref(block['preview_asset']))
    for motion in ident.get('motion',[]):
        for k in ('asset_id','reduced_motion_asset'):r.run('integrity','MOTION_REFERENCE',lambda motion=motion,k=k:asset_ref(motion[k]))
        r.run('brand_rules','REDUCED_MOTION',lambda motion=motion:check(asset_ref(motion['reduced_motion_asset'])['media_type'] in ('image/svg+xml','image/png','image/jpeg'),'reduced-motion fallback must be a static image'))
    for sound in ident.get('sound',[]):
        r.run('integrity','SOUND_REFERENCE',lambda sound=sound:check(asset_ref(sound['asset_id'])['media_type'].startswith('audio/'),'sound must reference audio'))
        a=assets.get(sound['asset_id'])
        if a and a['availability']=='present' and a['path'].endswith('.wav'):
            def duration(a=a,sound=sound):
                with wave.open(str(local(pack,a['path'])),'rb') as wav:
                    actual=1000*wav.getnframes()/wav.getframerate()
                check(abs(actual-sound['duration_ms'])<=2,'audio duration mismatch')
            r.run('integrity','SOUND_DURATION',duration)
    locales=ident.get('localization',[]);locale_ids={x['locale'] for x in locales};tfids={x['id'] for x in ident.get('typography',[])}
    r.run('structure','LOCALE_IDS',lambda:unique(locales,'locale'))
    for loc in locales:
        r.run('integrity','LOCALE_TYPEFACES',lambda loc=loc:check(set(loc['typeface_ids'])<=tfids,'unknown locale typeface'))
        if 'wordmark_asset' in loc:r.run('integrity','LOCALIZED_MARK',lambda loc=loc:asset_ref(loc['wordmark_asset']))
        if 'fallback_locale' in loc:r.run('integrity','LOCALE_FALLBACK',lambda loc=loc:check(loc['fallback_locale'] in locale_ids,'unknown locale fallback'))
    r.run('integrity','LOCALE_GRAPH',lambda:graph({l['locale']:[l['fallback_locale']] if 'fallback_locale' in l else [] for l in locales},'locale'))
    for rel in ident.get('relationships',[]):
        r.run('structure','SELF_RELATION',lambda rel=rel:check(rel['brand_id']!=ident['id'],'self brand relationship forbidden'))
        r.add('completeness','EXTERNAL_BRAND',rel['id']+': pinned reference; no automatic inheritance or network fetch','warning')
    for claim in ident.get('verbal',{}).get('claims',[]):
        if claim['status']=='approved':
            r.run('integrity','CLAIM_EVIDENCE',lambda claim=claim:local(pack,claim.get('evidence','')))
            r.add('approval','CLAIM_UNVERIFIED',claim['id']+': pack claim status is not independently authorized','warning')
    for ev in ident.get('evidence',[]):
        r.run('integrity','EVIDENCE_HASH',lambda ev=ev:check(sha(local(pack,ev['path']))==ev['sha256'],'evidence hash mismatch'))
        for subject in ev['subjects']:
            r.run('integrity','EVIDENCE_SUBJECT',lambda subject=subject:check(asset_ref(subject['id']).get('sha256')==subject['sha256'],'evidence covers stale asset'))
        r.add('rendering','DECLARED_EVIDENCE',ev['id']+': '+ev['status']+' via '+ev['method']+' (recorded, not rerun)', 'warning')
    apply_rules(pack,ident,assets,r)
    verify_approvals(pack,ident,assets,trust_path,r)
    return r.finish()

