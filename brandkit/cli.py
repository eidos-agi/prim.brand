from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from .io import Invalid, load
from .validate import validate
from .operations import compile_tokens,inventory,select,release,verify_release,bundle,diff,preview,migrate
from .schema import write_schemas
from .export import export_asset


def main(argv=None):
    p=argparse.ArgumentParser(description='prim.brand v0.2 — local tools; no arbitrary pack execution')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('validate','inventory','select','compile','release','verify-release','bundle','preview','migrate','diff'):
        s=sub.add_parser(name);s.add_argument('pack',type=Path)
        if name in ('validate','inventory','select','verify-release'):s.add_argument('--trust',type=Path)
        if name in ('inventory','select'):s.add_argument('--filters',default='{}',help='JSON object; ambiguous selections fail')
        if name in ('release','bundle','preview','migrate'):s.add_argument('target',type=Path)
        if name=='verify-release':s.add_argument('manifest',type=Path)
        if name=='diff':s.add_argument('after',type=Path)
    s=sub.add_parser('export');s.add_argument('pack',type=Path);s.add_argument('asset_id');s.add_argument('target',type=Path);s.add_argument('--width',type=int);s.add_argument('--trust',type=Path)
    s=sub.add_parser('schemas');s.add_argument('root',type=Path)
    args=p.parse_args(argv)
    try:
        if args.command=='export':result=export_asset(args.pack,args.asset_id,args.target,args.width,args.trust)
        elif args.command=='validate':result=validate(args.pack,args.trust)
        elif args.command=='compile':result=compile_tokens(args.pack)
        elif args.command=='inventory':result=inventory(args.pack,json.loads(args.filters),args.trust)
        elif args.command=='select':result=select(args.pack,json.loads(args.filters),args.trust)
        elif args.command=='verify-release':result=verify_release(args.pack,args.manifest,args.trust)
        elif args.command=='diff':result=diff(args.pack,args.after)
        elif args.command=='schemas':write_schemas(args.root);result={'written':True}
        else:result={'release':release,'bundle':bundle,'preview':preview,'migrate':migrate}[args.command](args.pack,args.target)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        if args.command=='validate':return 0 if result['passed'] else 1
        if args.command=='verify-release':return 0 if result['ready_for_use'] else 1
        return 0
    except (Invalid,OSError,ValueError,RecursionError) as e:
        print(json.dumps({'error':str(e)}));return 2

if __name__=='__main__':sys.exit(main())
