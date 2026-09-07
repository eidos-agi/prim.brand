import copy,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from brandkit.io import Invalid,save,load,sha
from brandkit.operations import migrate
from brandkit.validate import validate
from brandkit.export import export_asset
from test_brand import fixture,ROOT

class HardeningTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.pack=self.base/'pack';self.i=fixture.minimal(self.pack)
    def tearDown(self):self.temp.cleanup()
    def test_svg_style_external_import_rejected(self):
        p=self.pack/'assets/mark.svg';p.write_text('<svg viewBox="0 0 64 64"><style>@import "https://example.invalid/a.css";</style></svg>');self.i['assets'][0]['sha256']=sha(p);save(self.pack/'identity.json',self.i)
        self.assertFalse(validate(self.pack)['passed'])
    def test_svg_inline_external_url_rejected(self):
        p=self.pack/'assets/mark.svg';p.write_text('<svg viewBox="0 0 64 64"><path style="fill:url(https://example.invalid/a)"/></svg>');self.i['assets'][0]['sha256']=sha(p);save(self.pack/'identity.json',self.i)
        self.assertFalse(validate(self.pack)['passed'])
    def test_export_respects_explicit_prohibition(self):
        self.i['assets'][0]['constraints']={'forbidden_transforms':['rasterize']};save(self.pack/'identity.json',self.i)
        with self.assertRaises(Invalid):export_asset(self.pack,'mark:primary',self.base/'out',64)
    def test_legacy_schema_header_and_inherited_types(self):
        old=self.base/'old';old.mkdir();(old/'index.md').write_text('---\nprofile: brand\ntype: kit\nbrand_version: "0.1.0"\ntitle: "Old"\n---\n');shutil.copytree(self.pack/'assets',old/'assets')
        legacy={'brand_version':'0.1.0','brand':{'id':'brand:old','display_name':'Old'},'logo':[{'id':'logo:old','path':'assets/mark.svg','sha256':sha(old/'assets/mark.svg')}],'typefaces':[]}
        tokens={'$schema':'https://tr.designtokens.org/format/','palette':{'$type':'color','ink':{'$value':'#010203'}},'size':{'radius':{'$type':'dimension','$value':'2px'}}}
        save(old/'identity.json',legacy);save(old/'tokens/dtcg.json',tokens);dest=self.base/'new';migrate(old,dest)
        self.assertTrue(validate(dest)['passed']);self.assertEqual(load(dest/'migration/legacy-tokens.json'),tokens)
        self.assertEqual(load(dest/'tokens/dtcg.json')['palette']['ink']['$value']['colorSpace'],'srgb')
    def test_stdio_rejects_nonfinite_json(self):
        proc=subprocess.run([sys.executable,str(ROOT/'tools/mcp.py'),str(self.pack)],input='{"jsonrpc":"2.0","id":1,"method":"ping","params":{"x":NaN}}\n',text=True,capture_output=True,timeout=10)
        self.assertEqual(json.loads(proc.stdout)['error']['code'],-32700)
