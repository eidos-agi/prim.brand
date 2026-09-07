"""Bounded asset export adapter. Never alters the pack or approves its own output."""
from __future__ import annotations
from pathlib import Path
import shutil
from importlib.metadata import version
from .io import Invalid,output_root,local,sha,save
from .operations import select,FONT_SUFFIXES
from .tokens import check


def export_asset(pack: Path,asset_id: str,target: Path,width: int|None=None,trust: Path|None=None):
    pack=Path(pack).resolve();asset=select(pack,{'id':asset_id},trust)
    source=local(pack,asset['path']);check(source.suffix.lower() not in FONT_SUFFIXES,'font redistribution is not supported')
    target=output_root(pack,target)
    if width is not None:check(type(width)==int and 1<=width<=8192,'width must be an integer in 1..8192')
    target.parent.mkdir(parents=True,exist_ok=True);target.mkdir()
    try:
        if width is None:
            output=target/('asset'+source.suffix);shutil.copyfile(source,output);operation='copy';tool='stdlib.shutil';tool_version='python-3'
        else:
            output=target/'asset.png'
            if asset['media_type']=='image/svg+xml':
                import cairosvg
                vb=asset.get('view_box')
                if not vb:
                    from defusedxml import ElementTree as ET
                    import re
                    vb=[float(x) for x in re.split(r'[ ,]+',ET.fromstring(source.read_bytes()).get('viewBox'))]
                height=round(width*vb[3]/vb[2]);check(1<=height<=8192,'output height exceeds limit')
                cairosvg.svg2png(url=str(source),write_to=str(output),output_width=width,output_height=height)
                operation='rasterize';tool='CairoSVG';tool_version=version('CairoSVG')
            elif asset['media_type'] in ('image/png','image/jpeg','image/webp'):
                from PIL import Image
                with Image.open(source) as im:
                    check(im.width*im.height<=64_000_000,'input image too large');height=round(width*im.height/im.width);check(1<=height<=8192,'output height exceeds limit')
                    im.resize((width,height),Image.Resampling.LANCZOS).save(output)
                operation='resize';tool='Pillow';tool_version=version('Pillow')
            else:raise Invalid('no raster export adapter for this media type')
        allowed=operation in asset.get('constraints',{}).get('allowed_transforms',[])
        record={'source_asset_id':asset_id,'source_sha256':asset['sha256'],'output':output.name,'sha256':sha(output),
          'operation':operation,'tool':tool,'version':tool_version,'parameters':{'width':width},
          'source_approval_verified':asset['verified_approval'],'within_declared_transforms':allowed,
          'approval':'candidate','note':'A correct export does not create an authorized approval record.'}
        save(target/'export-record.json',record);return record
    except Exception:
        shutil.rmtree(target);raise
