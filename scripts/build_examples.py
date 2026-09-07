#!/usr/bin/env python3
"""Synthetic public conformance fixtures. Never import a private brand here."""
from pathlib import Path
import copy
import json
import shutil
import sys
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from brandkit.io import save,sha
from brandkit.operations import compile_tokens
from brandkit.validate import asset_digest


def minimal(root: Path):
    root.mkdir(parents=True,exist_ok=True);(root/'assets').mkdir(exist_ok=True)
    (root/'assets/mark.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path fill="#6c8aff" d="M8 8H56V56H8Z"/></svg>\n','utf-8')
    asset={'id':'mark:primary','role':'master','purpose':'logo','media_type':'image/svg+xml','representation':'vector','availability':'present','required':True,'path':'assets/mark.svg','sha256':sha(root/'assets/mark.svg'),'view_box':[0,0,64,64],'background':'transparent','editable':'geometry','approval':'candidate','rights':{'status':'declared','license':'CC0-1.0','redistribution':'allowed'}}
    identity={'profile':'brand','brand_version':'0.2.0','identity_version':'1.0.0','id':'brand:example','name':'Example Brand','status':'draft','capabilities':['visual'],'required_capabilities':['visual'],'assets':[asset],'rules':[],'deliverables':[{'id':'deliverable:logo','asset_id':'mark:primary','required':True,'purpose':'Primary mark'}],'visual':{'primary_asset':'mark:primary','usage':['Synthetic fixture, not an approved commercial identity.']}}
    save(root/'identity.json',identity)
    (root/'index.md').write_text('---\nprofile: brand\ntype: kit\nbrand_version: "0.2.0"\ntitle: "Example Brand"\nstatus: draft\n---\n\nMinimal, logo-only brand prim.\n','utf-8')
    (root/'log.md').write_text('# Change log\n\nSynthetic fixture created for conformance testing.\n','utf-8')
    return identity


def comprehensive(root: Path):
    identity=minimal(root);identity['capabilities']=['visual','tokens','typography','verbal','templates','motion','sound','localization','relationships','lineage','approvals']
    def asset(path,aid,mime,representation,**extra):
        a={'id':aid,'role':'support','purpose':aid,'media_type':mime,'representation':representation,'availability':'present','required':False,'path':path,'sha256':sha(root/path),'background':'not-applicable','editable':'none','approval':'unreviewed','rights':{'status':'declared','license':'CC0-1.0','redistribution':'allowed'},**extra}
        identity['assets'].append(a);return a
    shutil.copyfile(root/'assets/mark.svg',root/'assets/mark-copy.svg')
    asset('assets/mark-copy.svg','mark:copy','image/svg+xml','vector',role='derivative',derived_from=[{'id':'mark:primary','sha256':identity['assets'][0]['sha256']}],recipe='recipe:copy',editable='geometry',background='transparent')
    identity['recipes']=[{'id':'recipe:copy','operation':'copy','tool':'stdlib.shutil','version':'python-3','parameters':{},'deterministic':True,'requires_review':False}]
    tokens={'palette':{'$type':'color','ink':{'$value':{'colorSpace':'srgb','components':[0.02,0.025,0.04]}},'paper':{'$value':{'colorSpace':'srgb','components':[0.96,0.97,0.99]}}},'space':{'$type':'dimension','md':{'$value':{'value':16,'unit':'px'}}},'type':{'body':{'$type':'fontFamily','$value':['system-ui','sans-serif']}},'motion':{'fast':{'$type':'duration','$value':{'value':180,'unit':'ms'}}}}
    save(root/'tokens/dtcg.json',tokens)
    for name,fg,bg in [('light','ink','paper'),('dark','paper','ink')]:
        save(root/f'tokens/{name}.json',{'text':{'$type':'color','$value':'{palette.'+fg+'}'},'surface':{'$type':'color','$value':'{palette.'+bg+'}'}})
    resolver={'version':'2025.10','sets':{'base':{'sources':[{'$ref':'dtcg.json'}]}},'modifiers':{'theme':{'contexts':{'light':[{'$ref':'light.json'}],'dark':[{'$ref':'dark.json'}]},'default':'light'}},'resolutionOrder':[{'$ref':'#/sets/base'},{'$ref':'#/modifiers/theme'}]}
    save(root/'tokens/resolver.json',resolver)
    identity['tokens']={'version':'2025.10','path':'tokens/dtcg.json','resolver':'tokens/resolver.json','modes':{'light':{'inputs':{'theme':'light'},'selector':':root'},'dark':{'inputs':{'theme':'dark'},'selector':'[data-palette="dark"]'}},'css':'kit.css','css_mapping':{'--brand-text':'text','--brand-surface':'surface','--brand-space':'space.md','--brand-type':'type.body','--brand-duration':'motion.fast'}}
    identity['typography']=[{'id':'type:system','family':'System UI','strategy':'system','roles':['body','ui'],'fallbacks':['system-ui','sans-serif']},{'id':'type:mark','family':'Outlined mark','strategy':'outlined','roles':['logo'],'asset_ids':['mark:primary']}]
    identity['verbal']={'positioning':'A synthetic conformance example.','tone':['clear','literal'],'preferred':['State what is known.'],'prohibited':['Invented performance claims.'],'claims':[]}
    (root/'blocks/hero').mkdir(parents=True,exist_ok=True)
    (root/'blocks/hero/block.html').write_text('<link rel="stylesheet" href="../../kit.css"><link rel="stylesheet" href="block.css"><section class="brand-hero"><h1>Example</h1><p>Content slot.</p></section>\n','utf-8')
    (root/'blocks/hero/block.css').write_text('.brand-hero { color: var(--brand-text); background: var(--brand-surface); padding: var(--brand-space); font-family: var(--brand-type); }\n','utf-8')
    identity['templates']=[{'id':'template:hero','name':'Hero','when':'First introduction.','refuses':['Unverified metrics.'],'states':['default'],'slots':[{'name':'title','required':True,'kind':'text'}],'implementation':{'kind':'html-css','html':'blocks/hero/block.html','css':'blocks/hero/block.css'},'preview_asset':'mark:primary'}]
    (root/'assets/entrance.css').write_text('@keyframes brand-enter { from { opacity: 0; } to { opacity: 1; } } .brand-enter { animation: brand-enter var(--brand-duration) 1; } @media(prefers-reduced-motion:reduce) { .brand-enter { animation:none; } }\n','utf-8')
    asset('assets/entrance.css','motion:entrance','text/css','data')
    identity['motion']=[{'id':'motion:appear','asset_id':'motion:entrance','duration_ms':180,'iterations':1,'reduced_motion_asset':'mark:primary','purpose':'Optional introduction; no idle loop.'}]
    with wave.open(str(root/'assets/silence.wav'),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(8000);wav.writeframes(b'\x00\x00'*640)
    asset('assets/silence.wav','sound:fixture','audio/wav','audio')
    identity['sound']=[{'id':'sound:cue','asset_id':'sound:fixture','duration_ms':80,'silent_alternative':'Display the same state in text.','autoplay':False,'purpose':'Silent synthetic fixture, not a production sonic signature.'}]
    identity['localization']=[{'locale':'en','direction':'ltr','wordmark_asset':'mark:primary','typeface_ids':['type:system'],'copy':{'title':'Example'}},{'locale':'fr','direction':'ltr','typeface_ids':['type:system'],'fallback_locale':'en','copy':{'title':'Exemple'}}]
    identity['relationships']=[{'id':'relationship:example','kind':'composition','brand_id':'brand:other','version':'1.0.0','identity_sha256':'0'*64,'uri':'urn:example:brand:other','allowed_overrides':[],'notes':'External synthetic reference; never fetched.'}]
    (root/'evidence').mkdir(exist_ok=True);(root/'evidence/decision.md').write_text('Synthetic test decision. It confers no production authority.\n','utf-8')
    decision={'id':'decision:example','principal':'example-owner','at':'2026-01-01T00:00:00Z','decision':'approve','scope':'reference','subjects':[{'asset_id':'mark:primary','sha256':identity['assets'][0]['sha256'],'record_sha256':asset_digest(identity['assets'][0])}],'evidence':{'path':'evidence/decision.md','sha256':sha(root/'evidence/decision.md')}}
    identity['approvals']={'path':'approvals.json'};save(root/'approvals.json',{'version':'0.2.0','decisions':[decision]})
    identity['rules']=[{'id':'rule:contrast','kind':'contrast','severity':'error','foreground':'#ffffff','background':'#000000','minimum':4.5}]
    save(root/'identity.json',identity);compile_tokens(root)
    return identity

if __name__=='__main__':
    base=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'examples'
    minimal(base/'minimal');comprehensive(base/'comprehensive')
