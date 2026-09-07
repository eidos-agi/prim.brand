from __future__ import annotations
from dataclasses import dataclass,field
from jsonschema import Draft202012Validator,FormatChecker
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from . import __version__
from .io import Invalid,digest
from .token_common import check

DIMENSIONS=('structure','integrity','completeness','brand_rules','rendering','approval')

@dataclass
class Report:
    findings: list = field(default_factory=list)
    checks: int = 0
    evaluated: set = field(default_factory=set)
    verified_assets: set = field(default_factory=set)
    required_assets: set = field(default_factory=set)
    identity: dict = field(default_factory=dict)
    def add(self,dimension,code,message,severity='error',path=''):
        self.findings.append(dict(dimension=dimension,code=code,severity=severity,path=path,message=str(message)))
    def run(self,dimension,code,fn,path=''):
        self.checks+=1;self.evaluated.add(dimension)
        try:return fn()
        except (Invalid,ValueError,KeyError,TypeError,OSError,RecursionError,ET.ParseError,DefusedXmlException) as e:
            self.add(dimension,code,str(e),path=path);return None
    def finish(self):
        dims={}
        for d in DIMENSIONS:
            rows=[f for f in self.findings if f['dimension']==d]
            dims[d]='failed' if any(f['severity']=='error' for f in rows) else 'warnings' if rows else 'passed' if d in self.evaluated else 'not-run'
        error=any(f['severity']=='error' for f in self.findings)
        conformant=not any(f['severity']=='error' and f['dimension'] in ('structure','integrity') for f in self.findings)
        required=self.required_assets
        return {'tool':'prim.brand','tool_version':__version__,'profile_version':self.identity.get('brand_version'),
         'brand_id':self.identity.get('id'),'passed':not error,'conformant':conformant,
         'ready_for_use':not error and bool(required) and required<=self.verified_assets,
         'dimensions':dims,'checks_executed':self.checks,'verified_assets':sorted(self.verified_assets),
         'required_assets':sorted(required),'findings':self.findings,
         'scope':'Local structural/integrity checks and declared evidence; not legal, platform, accessibility or design certification.'}

def schema_errors(data,schema):
    return sorted(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(data),key=lambda e:str(list(e.path)))

def assert_schema(data,schema):
    problems=schema_errors(data,schema)
    check(not problems, '; '.join('/'+'/'.join(map(str,e.path))+': '+e.message for e in problems[:8]))

def unique(records,key='id'):
    values=[v[key] for v in records]
    check(len(set(values))==len(values),f'duplicate {key}')

def asset_digest(asset):
    return digest({k:v for k,v in asset.items() if k!='approval'})

def graph(edges,label):
    done=set()
    def visit(node,active):
        check(node not in active and len(active)<128,label+' cycle/limit')
        if node in done:return
        for child in edges.get(node,[]):visit(child,active|{node})
        done.add(node)
    for node in edges:visit(node,set())

