from __future__ import annotations
from html.parser import HTMLParser
import re,struct,wave,zipfile
import tinycss2
from defusedxml import ElementTree as ET
from .io import local,sha
from .token_common import check

class SafeHTML(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.urls=[]
    def handle_starttag(self,tag,attrs):
        check(tag not in {'script','iframe','object','embed','base'},'active HTML is not allowed')
        for k,v in attrs:
            check(not k.lower().startswith('on'),'event handler forbidden')
            check(k not in {'srcdoc','style','srcset'},'inline content/style or srcset forbidden in reference block')
            if k in {'href','src','action','poster'} and v:
                check(not re.match(r'(?i)\s*(?:[a-z][a-z0-9+.-]*:|//)',v),'external HTML dependency forbidden')
                self.urls.append(v)
    handle_startendtag=handle_starttag

def css_scan(text,variables,token_only=False):
    def walk(nodes):
        for t in nodes:
            check(t.type!='error','invalid CSS syntax')
            if t.type=='at-keyword':check(t.value.lower() not in {'import','namespace'},'external CSS directive forbidden')
            if t.type=='url':check(t.value.startswith('#'),'CSS resource loading forbidden')
            if t.type=='function':
                check(t.lower_name not in {'url','expression'},'CSS resource/expression forbidden')
                if t.lower_name=='var':
                    items=[x for x in t.arguments if x.type not in {'whitespace','comment'}]
                    check(items and items[0].type=='ident' and items[0].value in variables,'CSS references undeclared token')
                walk(t.arguments)
            if token_only:
                check(t.type!='hash','literal color outside token projection')
                check(not(t.type=='dimension' and t.value!=0),'nonzero dimensional literal outside token projection')
                if t.type=='function':check(t.lower_name not in {'rgb','rgba','hsl','hsla','hwb','lab','lch','oklab','oklch','color'},'literal color function outside token projection')
            if hasattr(t,'content') and t.content is not None:walk(t.content)
    walk(tinycss2.parse_component_value_list(text))

def inspect_asset(pack,asset):
    p=local(pack,asset['path']);check(sha(p)==asset['sha256'],'content hash mismatch')
    suffix=p.suffix.lower();mime=asset['media_type']
    if mime.startswith('font/'):
        magic=p.read_bytes()[:4]
        check(magic in (b'\x00\x01\x00\x00',b'OTTO',b'ttcf',b'wOFF',b'wOF2'),'invalid font container signature')
    if suffix in ('.png','.jpg','.jpeg','.webp','.ico','.icns'):
        from PIL import Image
        expected={'.png':'PNG','.jpg':'JPEG','.jpeg':'JPEG','.webp':'WEBP','.ico':'ICO','.icns':'ICNS'}[suffix]
        with Image.open(p) as image:
            check(image.format==expected,'raster container does not match extension')
            check(image.width*image.height<=64_000_000,'raster pixel limit')
            width,height=image.size
            image.verify()
        with Image.open(p) as image:image.load()
        if 'width' in asset:check(width==asset['width'],'raster width mismatch')
        if 'height' in asset:check(height==asset['height'],'raster height mismatch')
        check(asset['representation']=='raster','raster representation mismatch')
        check(asset['editable'] in ('none','unknown'),'flat raster cannot claim editable layers or text')
    check(not suffix in {'.ttf','.otf','.woff','.woff2'} or mime.startswith('font/'),'font MIME mismatch')
    if suffix=='.svg':
        check(mime=='image/svg+xml','SVG MIME mismatch')
        root=ET.fromstring(p.read_bytes());check(root.tag.split('}')[-1]=='svg','not an SVG document')
        tags={node.tag.split('}')[-1] for node in root.iter()}
        check(not tags & {'script','foreignObject','iframe','object','embed'},'active SVG element forbidden')
        for node in root.iter():
            if node.tag.split('}')[-1]=='style':css_scan(node.text or '',set())
            for key,val in node.attrib.items():
                k=key.split('}')[-1].lower()
                if k=='style':css_scan(val,set())
                check(not k.startswith('on'),'SVG event handler forbidden')
                if k=='href':check(val.startswith('#'),'external/embedded SVG dependency forbidden')
                if 'url(' in val:
                    for ref in re.findall(r'url\((.*?)\)',val):check(ref.strip().strip("\"'").startswith('#'),'non-local SVG URL forbidden')
        if asset['representation']=='vector':check('image' not in tags,'bitmap wrapped in a claimed vector')
        if asset['representation']=='raster':check(False,'SVG may be vector or mixed, not a raster file')
        vb=[float(x) for x in re.split(r'[ ,]+',root.get('viewBox','').strip()) if x]
        check(len(vb)==4 and all(__import__('math').isfinite(v) for v in vb) and vb[2]>0 and vb[3]>0,'invalid SVG viewBox')
        if 'view_box' in asset:check(vb==asset['view_box'],'declared viewBox differs')
        for key in ('width','height'):
            if key in asset and root.get(key) and re.fullmatch(r'[0-9.]+(?:px)?',root.get(key)):
                check(float(root.get(key).removesuffix('px'))==asset[key],'SVG declared size differs')
        if asset['editable']=='text':check('text' in tags,'outlined lettering is not editable text')
    elif suffix=='.png':
        check(mime=='image/png' and asset['representation']=='raster','PNG MIME/representation mismatch')
        b=p.read_bytes();check(b[:8]==b'\x89PNG\r\n\x1a\n' and b[12:16]==b'IHDR','invalid PNG header')
        w,h=struct.unpack('>II',b[16:24]);check(w>0 and h>0,'invalid PNG dimensions')
        if 'width' in asset:check(w==asset['width'],'PNG width mismatch')
        if 'height' in asset:check(h==asset['height'],'PNG height mismatch')
        check(asset['editable'] in ('none','unknown'),'flat PNG cannot claim text/layer editability')
    elif suffix=='.pdf':check(mime=='application/pdf' and p.read_bytes()[:5]==b'%PDF-','PDF magic/MIME mismatch')
    elif suffix in ('.jpg','.jpeg'):check(mime=='image/jpeg' and p.read_bytes()[:3]==b'\xff\xd8\xff','JPEG magic/MIME mismatch')
    elif suffix=='.wav':
        check(mime in ('audio/wav','audio/x-wav'),'WAV MIME mismatch')
        with wave.open(str(p),'rb') as wav:check(wav.getnframes()>0 and wav.getframerate()>0,'empty/invalid WAV')
    elif suffix=='.pptx':
        check(mime=='application/vnd.openxmlformats-officedocument.presentationml.presentation','PPTX MIME mismatch')
        with zipfile.ZipFile(p) as z:check('ppt/presentation.xml' in z.namelist(),'not a PPTX container')
    else:
        if asset['representation']=='vector':check(False,'unrecognized vector format cannot be certified')
    return True

