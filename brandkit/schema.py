"""JSON Schema 2020-12 contract. Generated schemas are committed for other readers."""
from __future__ import annotations
from pathlib import Path
from .io import save

STR={'type':'string','minLength':1}
ID={'type':'string','pattern':r'^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$'}
HASH={'type':'string','pattern':'^[a-f0-9]{64}$'}
PATH={'type':'string','minLength':1,'pattern':r'^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[^\\\x00:%?#]+$'}
NUM={'type':'number','minimum':0}
POS={'type':'number','exclusiveMinimum':0}
BOOL={'type':'boolean'}
DATE={'type':'string','format':'date-time'}

def array(item, minimum=0): return {'type':'array','items':item,'minItems':minimum}
def enum(*values): return {'enum':list(values)}
def obj(properties,required=()):
    return {'type':'object','properties':properties,'required':list(required),'additionalProperties':False}
def ref(name): return {'$ref':'#/$defs/'+name}

REF=obj({'id':ID,'sha256':HASH},['id','sha256'])
ASSET=obj({
 'id':ID,'role':enum('master','derivative','reference','mockup','template','export','support'),
 'purpose':STR,'media_type':STR,'representation':enum('vector','raster','mixed','document','audio','video','data'),
 'availability':enum('present','external','planned','missing'), 'required':BOOL,
 'path':PATH,'uri':{'type':'string','format':'uri','pattern':'^https://'},'sha256':HASH,
 'width':POS,'height':POS,'view_box':{'type':'array','items':{'type':'number'},'minItems':4,'maxItems':4},
 'background':enum('transparent','dark','light','color','not-applicable','unknown'),
 'editable':enum('none','geometry','text','layers','slides','unknown'),
 'approval':enum('unreviewed','candidate','approved','rejected','superseded'),
 'rights':obj({'status':enum('declared','unknown','restricted'),'license':STR,'evidence':PATH,'redistribution':enum('allowed','forbidden','unknown')},['status','redistribution']),
 'derived_from':array(REF),'recipe':ID,'notes':STR,
 'constraints':obj({'backgrounds':array(STR),'min_px':POS,'clear_space':STR,'allowed_transforms':array(STR),'forbidden_transforms':array(STR)})
},['id','role','purpose','media_type','representation','availability','required','background','editable','approval','rights'])
ASSET['allOf']=[
 {'if':{'properties':{'availability':{'const':'present'}}},'then':{'required':['path','sha256']}},
 {'if':{'properties':{'availability':{'const':'external'}}},'then':{'required':['uri','sha256']}},
 {'if':{'properties':{'role':{'enum':['derivative','export']}}},'then':{'required':['derived_from','recipe'],'properties':{'derived_from':{'minItems':1}}}}
]
TYPEFACE=obj({'id':ID,'family':STR,'strategy':enum('bundled','reference','system','outlined'),
 'roles':array(STR,1),'asset_ids':array(ID),'license':STR,'license_path':PATH,'uri':{'type':'string','format':'uri','pattern':'^https://'},
 'fallbacks':array(STR),'notes':STR},['id','family','strategy','roles'])
TYPEFACE['allOf']=[
 {'if':{'properties':{'strategy':{'const':'bundled'}}},'then':{'required':['asset_ids','license','license_path'],'properties':{'asset_ids':{'minItems':1}}}},
 {'if':{'properties':{'strategy':{'const':'reference'}}},'then':{'required':['uri','fallbacks'],'properties':{'fallbacks':{'minItems':1}}}},
 {'if':{'properties':{'strategy':{'const':'system'}}},'then':{'required':['fallbacks'],'properties':{'fallbacks':{'minItems':1}}}},
 {'if':{'properties':{'strategy':{'const':'outlined'}}},'then':{'required':['asset_ids'],'properties':{'asset_ids':{'minItems':1}}}}
]
TEMPLATE=obj({'id':ID,'name':STR,'when':STR,'refuses':array(STR),'states':array(STR,1),
 'slots':array(obj({'name':ID,'required':BOOL,'kind':enum('text','asset','list')},['name','required','kind'])),
 'implementation':obj({'kind':enum('html-css','external'),'html':PATH,'css':PATH,'uri':{'type':'string','format':'uri','pattern':'^https://'},'sha256':HASH},['kind']),
 'preview_asset':ID},['id','name','when','refuses','states','slots','implementation'])
TEMPLATE['properties']['implementation']['allOf']=[
 {'if':{'properties':{'kind':{'const':'html-css'}}},'then':{'required':['html','css']}},
 {'if':{'properties':{'kind':{'const':'external'}}},'then':{'required':['uri','sha256']}}
]
RECIPE=obj({'id':ID,'operation':enum('copy','resize','rasterize','reconstruct','generate','convert','compose'),
 'tool':STR,'version':STR,'parameters':{'type':'object'},'deterministic':BOOL,
 'requires_review':BOOL,'allowed_by':array(ID)},['id','operation','tool','version','parameters','deterministic','requires_review'])
SUBJECT=obj({'asset_id':ID,'sha256':HASH,'record_sha256':HASH},['asset_id','sha256','record_sha256'])
APPROVAL=obj({'id':ID,'principal':STR,'at':DATE,'decision':enum('approve','reject','supersede'),
 'scope':enum('reference','asset','release'),'subjects':array(SUBJECT),'release_sha256':HASH,
 'evidence':obj({'path':PATH,'sha256':HASH},['path','sha256']), 'notes':STR},['id','principal','at','decision','scope','evidence'])
APPROVAL['allOf']=[
 {'if':{'properties':{'scope':{'const':'release'}}},'then':{'required':['release_sha256']}},
 {'if':{'properties':{'scope':{'enum':['reference','asset']}}},'then':{'required':['subjects'],'properties':{'subjects':{'minItems':1}}}}
]
MOTION=obj({'id':ID,'asset_id':ID,'duration_ms':POS,'iterations':{'type':'integer','minimum':1,'maximum':10},'reduced_motion_asset':ID,'purpose':STR},['id','asset_id','duration_ms','iterations','reduced_motion_asset','purpose'])
SOUND=obj({'id':ID,'asset_id':ID,'duration_ms':POS,'silent_alternative':STR,'autoplay':{'const':False},'purpose':STR},['id','asset_id','duration_ms','silent_alternative','autoplay','purpose'])
LOCALIZATION=obj({'locale':STR,'direction':enum('ltr','rtl'),'wordmark_asset':ID,'typeface_ids':array(ID),'fallback_locale':STR,'copy':{'type':'object','additionalProperties':STR}},['locale','direction','typeface_ids','copy'])
RELATION=obj({'id':ID,'kind':enum('parent','sub-brand','endorsement','co-brand','composition'),
 'brand_id':ID,'version':STR,'identity_sha256':HASH,'uri':{'type':'string','format':'uri'},
 'allowed_overrides':array(STR),'notes':STR},['id','kind','brand_id','version','identity_sha256','uri','allowed_overrides'])
RULE=obj({'id':ID,'kind':enum('forbidden-color','contrast','prohibited-term','asset-usage'),
 'severity':enum('error','warning'),'paths':array(PATH),'value':STR,'foreground':STR,'background':STR,'minimum':POS,'asset_id':ID,'notes':STR},['id','kind','severity'])
RULE['allOf']=[
 {'if':{'properties':{'kind':{'enum':['forbidden-color','prohibited-term']}}},'then':{'required':['paths','value'],'properties':{'paths':{'minItems':1}}}},
 {'if':{'properties':{'kind':{'const':'contrast'}}},'then':{'required':['foreground','background','minimum']}},
 {'if':{'properties':{'kind':{'const':'asset-usage'}}},'then':{'required':['asset_id','notes']}}
]
CAPABILITIES=['visual','tokens','typography','verbal','templates','motion','sound','localization','relationships','lineage','approvals']
PROPERTIES={
 '$schema':STR,'profile':{'const':'brand'},'brand_version':{'const':'0.2.0'},
 'identity_version':{'type':'string','pattern':r'^\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?$'},
 'id':ID,'name':STR,'status':enum('draft','active','deprecated'),
 'capabilities':dict(array(ID),uniqueItems=True),'required_capabilities':dict(array(ID),uniqueItems=True),
 'assets':array(ref('asset')),'rules':array(ref('rule')),'recipes':array(ref('recipe')),
 'visual':obj({'primary_asset':ID,'usage':array(STR)},['primary_asset','usage']),
 'tokens':obj({'version':{'const':'2025.10'},'path':PATH,'resolver':PATH,
  'modes':{'type':'object','minProperties':1,'additionalProperties':obj({'inputs':{'type':'object','additionalProperties':STR},'selector':STR},['inputs','selector'])},
  'css':PATH,'css_mapping':{'type':'object','minProperties':1,'propertyNames':{'pattern':'^--[a-zA-Z][a-zA-Z0-9_-]*$'},'additionalProperties':STR}},['version','path','modes','css','css_mapping']),
 'typography':array(ref('typeface'),1),
 'verbal':obj({'positioning':STR,'tone':array(STR,1),'preferred':array(STR),'prohibited':array(STR),
  'claims':array(obj({'id':ID,'text':STR,'status':enum('proposed','approved','rejected'),'evidence':PATH},['id','text','status']))},['positioning','tone','preferred','prohibited','claims']),
 'templates':array(ref('template'),1),'motion':array(ref('motion'),1),'sound':array(ref('sound'),1),
 'localization':array(ref('localization'),1),'relationships':array(ref('relationship'),1),
 'approvals':obj({'path':PATH},['path']),
 'deliverables':array(obj({'id':ID,'asset_id':ID,'required':BOOL,'purpose':STR},['id','asset_id','required','purpose'])),
 'evidence':array(obj({'id':ID,'kind':enum('render','test','fidelity','rights','accessibility'), 'path':PATH,'sha256':HASH,'subjects':array(REF,1),'status':enum('passed','failed','not-run'),'method':STR},['id','kind','path','sha256','subjects','status','method'])),
 'extensions':{'type':'object','propertyNames':{'pattern':'^[a-zA-Z0-9]+[.:][a-zA-Z0-9._:-]+$'},'additionalProperties':{'type':'object'}}
}
SCHEMA=dict(obj(PROPERTIES,['profile','brand_version','identity_version','id','name','status','capabilities','required_capabilities','assets','rules','deliverables']),
 **{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'https://schemas.prims.sh/brand/0.2.0/identity.schema.json',
 '$defs':{'asset':ASSET,'typeface':TYPEFACE,'template':TEMPLATE,'recipe':RECIPE,'motion':MOTION,'sound':SOUND,'localization':LOCALIZATION,'relationship':RELATION,'rule':RULE}})
SCHEMA['allOf']=[]
for cap in CAPABILITIES:
    field='recipes' if cap=='lineage' else cap
    SCHEMA['allOf'].append({'if':{'properties':{'capabilities':{'contains':{'const':cap}}}},'then':{'required':[field]}})
    SCHEMA['allOf'].append({'if':{'required':[field]},'then':{'properties':{'capabilities':{'contains':{'const':cap}}}}})
APPROVAL_SCHEMA=dict(obj({'version':{'const':'0.2.0'},'decisions':array(APPROVAL)},['version','decisions']),**{'$schema':'https://json-schema.org/draft/2020-12/schema'})
TRUST_SCHEMA=obj({'version':{'const':'0.2.0'},'trusted_decisions':array(obj({'sha256':HASH,'principal':STR,'scopes':array(enum('reference','asset','release'),1)},['sha256','principal','scopes'])),'revoked':array(HASH)},['version','trusted_decisions','revoked'])

def write_schemas(root: Path):
    save(root/'schemas/brand-0.2.schema.json',SCHEMA)
    save(root/'schemas/approvals-0.2.schema.json',APPROVAL_SCHEMA)
    save(root/'schemas/trust-0.2.schema.json',TRUST_SCHEMA)
