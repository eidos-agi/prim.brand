#!/usr/bin/env python3
"""Exercise public fixtures and unchanged historical packs; emit exact evidence."""
from pathlib import Path
import hashlib,json,platform,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from brandkit.io import save,sha,files
from brandkit.schema import write_schemas
from brandkit.validate import validate
from brandkit.operations import migrate,release,verify_release,bundle
from build_examples import minimal,comprehensive

def main():
    write_schemas(ROOT);minimal(ROOT/'examples/minimal');comprehensive(ROOT/'examples/comprehensive')
    tests=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(verbosity=2).run(tests)
    if not result.wasSuccessful():return 1
    report={'python':platform.python_version(),'tests_run':result.testsRun,'tests_passed':True,'fixtures':{},'legacy':{},'migration':{},'source_sha256':{}}
    for name in ('minimal','comprehensive'):
        item=validate(ROOT/'examples'/name)
        if not item['passed']:raise RuntimeError(json.dumps(item))
        report['fixtures'][name]={'passed':item['passed'],'checks':item['checks_executed'],'ready_for_use':item['ready_for_use']}
    with tempfile.TemporaryDirectory() as temp:
        for name in ('eidos','prim'):
            source=ROOT/'packs'/name
            before={p:sha(source/p) for p in files(source)}
            run=subprocess.run([sys.executable,str(ROOT/'scripts/validate.py'),str(source)],capture_output=True,text=True,check=True)
            report['legacy'][name]={'passed':True,'stdout':run.stdout.strip(),'files_unchanged':True}
            target=Path(temp)/name;converted=migrate(source,target)
            after={p:sha(source/p) for p in files(source)}
            if before!=after:raise RuntimeError('Legacy pack was modified')
            report['migration'][name]={'passed':converted['report']['passed'],'actions':converted['actions'],'source_unchanged':True}
        a=bundle(ROOT/'examples/minimal',Path(temp)/'a.zip');b=bundle(ROOT/'examples/minimal',Path(temp)/'b.zip')
        if a['sha256']!=b['sha256']:raise RuntimeError('Non-deterministic ZIP')
        report['deterministic_bundle']=True
    for folder in ('brandkit','tools','tests','scripts'):
        for p in sorted((ROOT/folder).glob('*.py')):report['source_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    save(ROOT/'reports'/f'conformance-python-{platform.python_version()}.json',report)
    print(json.dumps({'tests':result.testsRun,'fixtures':'passed','legacy':'passed','migration':'passed','deterministic_bundle':True}))
    return 0
if __name__=='__main__':sys.exit(main())
