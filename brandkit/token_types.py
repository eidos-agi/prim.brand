from __future__ import annotations
import json,re
from .token_common import check,numeric,SPACES,WEIGHTS

def validate_value(kind,v):
    def required(names):check(isinstance(v,dict) and set(names)<=set(v),f'invalid {kind} fields')
    if kind=='color':
        required(['colorSpace','components'])
        check(v['colorSpace'] in SPACES,'unknown color space')
        check(isinstance(v['components'],list) and len(v['components'])==3 and all(numeric(n) or n=='none' for n in v['components']),'invalid color components')
        check(numeric(v.get('alpha',1)) and 0<=v.get('alpha',1)<=1,'alpha outside [0,1]')
        if 'hex' in v:check(bool(re.fullmatch(r'#[0-9a-fA-F]{6}',v['hex'])),'invalid fallback hex')
    elif kind in ('dimension','duration'):
        required(['value','unit']);check(numeric(v['value']),'non-numeric dimension/duration')
        check(v['unit'] in (('px','rem') if kind=='dimension' else ('ms','s')),'invalid unit')
        if kind=='duration':check(v['value']>=0,'negative duration')
    elif kind=='number':check(numeric(v),'invalid number')
    elif kind=='fontFamily':check((isinstance(v,str) and v) or (isinstance(v,list) and v and all(isinstance(x,str) and x for x in v)),'invalid font family')
    elif kind=='fontWeight':check((numeric(v) and 1<=v<=1000) or (isinstance(v,str) and v in WEIGHTS),'invalid font weight')
    elif kind=='cubicBezier':check(isinstance(v,list) and len(v)==4 and all(numeric(n) for n in v) and 0<=v[0]<=1 and 0<=v[2]<=1,'invalid cubicBezier')
    elif kind=='strokeStyle':
        if isinstance(v,str):check(v in {'solid','dashed','dotted','double','groove','ridge','outset','inset'},'invalid stroke style')
        else:
            required(['dashArray','lineCap']);check(isinstance(v['dashArray'],list) and v['dashArray'],'invalid dashArray')
            check(v['lineCap'] in {'round','butt','square'},'invalid lineCap')
            for x in v['dashArray']:validate_value('dimension',x)
    elif kind in ('border','transition','typography'):
        fields={'border':{'color':'color','width':'dimension','style':'strokeStyle'},
          'transition':{'duration':'duration','delay':'duration','timingFunction':'cubicBezier'},
          'typography':{'fontFamily':'fontFamily','fontSize':'dimension','fontWeight':'fontWeight','letterSpacing':'dimension','lineHeight':'number'}}[kind]
        required(fields)
        for key,t in fields.items():validate_value(t,v[key])
    elif kind=='shadow':
        if isinstance(v,list):
            check(v,'empty shadow');[validate_value('shadow',x) for x in v];return
        required(['color','offsetX','offsetY','blur','spread']);validate_value('color',v['color'])
        for key in ('offsetX','offsetY','blur','spread'):validate_value('dimension',v[key])
        if 'inset' in v:check(type(v['inset'])==bool,'inset must be bool')
    elif kind=='gradient':
        check(isinstance(v,list) and v,'invalid gradient')
        for stop in v:
            check(isinstance(stop,dict) and {'color','position'}<=set(stop),'invalid gradient stop')
            validate_value('color',stop['color']);check(numeric(stop['position']) and 0<=stop['position']<=1,'invalid stop position')


def css_value(kind,v):
    validate_value(kind,v)
    if kind=='color':
        space=v['colorSpace'];components=' '.join(str(n) for n in v['components']);alpha=v.get('alpha',1)
        if space in {'hsl','hwb'}:
            c=v['components'];components=f'{c[0]} {c[1]}% {c[2]}%'
            return f'{space}({components} / {alpha})'
        if space in {'lab','lch','oklab','oklch'}:return f'{space}({components} / {alpha})'
        return f'color({space} {components} / {alpha})'
    if kind in ('dimension','duration'):return str(v['value'])+v['unit']
    if kind in ('number','fontWeight'):return str(v)
    if kind=='fontFamily':return ', '.join(json.dumps(x,ensure_ascii=False) for x in ([v] if isinstance(v,str) else v))
    if kind=='cubicBezier':return 'cubic-bezier('+','.join(str(n) for n in v)+')'
    if kind=='strokeStyle':
        check(isinstance(v,str),'dash-array stroke has no lossless single CSS projection')
        return v
    if kind=='border':return f'{css_value("dimension",v["width"])} {css_value("strokeStyle",v["style"])} {css_value("color",v["color"])}'
    if kind=='transition':return ' '.join(css_value(k,v[n]) for n,k in [('duration','duration'),('timingFunction','cubicBezier'),('delay','duration')])
    if kind=='gradient':return 'linear-gradient('+', '.join(css_value('color',s['color'])+' '+str(s['position']*100)+'%' for s in v)+')'
    if kind=='shadow':
        if isinstance(v,list):return ', '.join(css_value('shadow',x) for x in v)
        return ('inset ' if v.get('inset') else '')+' '.join(css_value('dimension',v[k]) for k in ('offsetX','offsetY','blur','spread'))+' '+css_value('color',v['color'])
    check(False,'composite typography requires individual property mappings, not a guessed font shorthand')

