"""Bounded, local-only reads, duplicate rejection, and canonical content digests."""
from __future__ import annotations
import hashlib
import json
import math
import os
import re
from pathlib import Path, PurePosixPath
import yaml

MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_FILE_BYTES = 128 * 1024 * 1024
MAX_FILES = 10000

class Invalid(ValueError):
    pass

def pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise Invalid(f"duplicate key: {key}")
        out[key] = value
    return out

class FaceLoader(yaml.SafeLoader):
    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise Invalid("YAML aliases are not supported in the face")
        return super().compose_node(parent, index)

def mapping(loader, node):
    return pairs([(loader.construct_object(k), loader.construct_object(v)) for k,v in node.value])
FaceLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
# Do not turn an ISO date into a Python object implicitly.
FaceLoader.yaml_implicit_resolvers = {
    k:[(tag,rx) for tag,rx in rows if tag != 'tag:yaml.org,2002:timestamp']
    for k,rows in FaceLoader.yaml_implicit_resolvers.items()
}

def local(root: Path, relative: str, exists: bool = True) -> Path:
    """Every component must remain local; reject symlinks, not just escaped targets."""
    root = Path(root).resolve()
    if not isinstance(relative,str) or not relative or any(c in relative for c in ('\\','\x00',':','%','?','#')):
        raise Invalid(f"unsafe relative path: {relative!r}")
    q = PurePosixPath(relative)
    if q.is_absolute() or any(p in ('..','.') for p in relative.split('/')) or '' in relative.split('/'):
        raise Invalid(f"unsafe relative path: {relative!r}")
    p = root
    for part in q.parts:
        p = p / part
        if p.is_symlink():
            raise Invalid(f"symlink is not allowed: {relative}")
    if not p.resolve().is_relative_to(root):
        raise Invalid(f"path escapes pack: {relative}")
    if exists and (not p.is_file() or p.stat().st_size > MAX_FILE_BYTES):
        raise Invalid(f"missing, non-regular or oversized file: {relative}")
    return p

def load(path: Path):
    path = Path(path)
    if path.stat().st_size > MAX_JSON_BYTES:
        raise Invalid(f"JSON exceeds limit: {path.name}")
    try:
        data = json.loads(path.read_text('utf-8'), object_pairs_hook=pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(Invalid(f"non-finite {value}")))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as e:
        raise Invalid(f"invalid JSON in {path.name}: {e}") from e
    budget=[100000]
    def walk(value, depth=0):
        budget[0]-=1
        if depth>80 or budget[0]<0: raise Invalid('document complexity limit')
        if isinstance(value,float) and not math.isfinite(value): raise Invalid('non-finite number')
        if isinstance(value,dict):
            for v in value.values(): walk(v,depth+1)
        if isinstance(value,list):
            for v in value: walk(v,depth+1)
    walk(data)
    return data

def face(root: Path):
    text = local(root,'index.md').read_text('utf-8')
    if len(text)>65536: raise Invalid('face exceeds 64 KiB')
    lines=text.splitlines()
    if not lines or lines[0]!='---': raise Invalid('face must start with YAML frontmatter')
    try: end=lines.index('---',1)
    except ValueError as e: raise Invalid('unterminated frontmatter') from e
    try: data=yaml.load('\n'.join(lines[1:end]),Loader=FaceLoader)
    except yaml.YAMLError as e: raise Invalid(f'invalid face: {e}') from e
    if not isinstance(data,dict): raise Invalid('face must be a mapping')
    if data.get('profile')!='brand' or data.get('type')!='kit': raise Invalid('face must declare profile: brand and type: kit')
    return data

def sha(path: Path) -> str:
    if path.stat().st_size>MAX_FILE_BYTES: raise Invalid('asset exceeds size limit')
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def canonical(value) -> bytes:
    # Spec-defined PBJ/1 encoding, deliberately not claimed to be RFC 8785 JCS.
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()

def save(path: Path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def files(root: Path):
    root=Path(root).resolve(); out=[]
    for folder, dirs, names in os.walk(root,followlinks=False):
        for d in dirs:
            if (Path(folder)/d).is_symlink(): raise Invalid('symlink directory in pack')
        for name in names:
            p=Path(folder)/name
            rel=p.relative_to(root).as_posix()
            local(root,rel)
            out.append(rel)
            if len(out)>MAX_FILES: raise Invalid('pack file count limit')
    return sorted(out)

def output_root(source: Path, target: Path) -> Path:
    """Operations never overwrite a source or write through a symlink."""
    source=Path(source).resolve(); target=Path(target).absolute()
    if any(p.is_symlink() for p in (target,*target.parents)): raise Invalid('symlink output path')
    target=target.resolve()
    if target.exists(): raise Invalid('destination already exists')
    if target.is_relative_to(source) or source.is_relative_to(target): raise Invalid('destination must be outside source')
    return target
