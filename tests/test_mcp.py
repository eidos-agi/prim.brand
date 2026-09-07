import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from brandkit.mcp import Server,PREFIX
from test_brand import fixture,ROOT

class MCPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.pack=Path(self.temp.name)/'pack';fixture.minimal(self.pack);self.server=Server(self.pack)
    def tearDown(self):self.temp.cleanup()
    def msg(self,method,**params):
        return {'jsonrpc':'2.0','id':1,'method':method,'params':{**params,'_meta':{PREFIX+'protocolVersion':'2026-07-28',PREFIX+'clientCapabilities':{}}}}
    def test_discover(self):
        r=self.server.handle(self.msg('server/discover'));self.assertIn('2026-07-28',r['result']['supportedVersions']);self.assertEqual(r['result']['resultType'],'complete')
    def test_modern_no_handshake(self):self.assertIn('tools',self.server.handle(self.msg('tools/list'))['result'])
    def test_missing_metadata(self):self.assertEqual(self.server.handle({'jsonrpc':'2.0','id':1,'method':'tools/list'})['error']['code'],-32602)
    def test_future_version(self):
        m=self.msg('server/discover');m['params']['_meta'][PREFIX+'protocolVersion']='2099-01-01';self.assertEqual(self.server.handle(m)['error']['code'],-32022)
    def test_required_capabilities(self):
        m=self.msg('tools/list');del m['params']['_meta'][PREFIX+'clientCapabilities'];self.assertEqual(self.server.handle(m)['error']['code'],-32602)
    def test_legacy(self):
        r=self.server.handle({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'test','version':'1'}}});self.assertEqual(r['result']['protocolVersion'],'2025-11-25')
        self.assertIsNone(self.server.handle({'jsonrpc':'2.0','method':'notifications/initialized'}))
        self.assertIn('tools',self.server.handle({'jsonrpc':'2.0','id':2,'method':'tools/list'})['result'])
    def test_call(self):
        r=self.server.handle(self.msg('tools/call',name='brand_select',arguments={'filters':{'id':'mark:primary'}}));self.assertFalse(r['result']['isError']);self.assertEqual(r['result']['structuredContent']['id'],'mark:primary')
    def test_no_arbitrary_path(self):
        r=self.server.handle(self.msg('tools/call',name='brand_assets',arguments={'path':'/etc/passwd'}));self.assertEqual(r['error']['code'],-32602)
    def test_no_writes(self):self.assertEqual(self.server.handle(self.msg('tools/call',name='brand_approve',arguments={}))['error']['code'],-32602)
    def test_bad_id(self):
        m=self.msg('ping');m['id']=None;self.assertEqual(self.server.handle(m)['error']['code'],-32600)
    def test_stdio(self):
        messages='\n'.join(json.dumps(self.msg(m)) for m in ['server/discover','tools/list'])+'\n'
        proc=subprocess.run([sys.executable,str(ROOT/'tools/mcp.py'),str(self.pack)],input=messages,text=True,capture_output=True,timeout=10)
        self.assertEqual(proc.returncode,0);rows=[json.loads(x) for x in proc.stdout.splitlines()];self.assertEqual(len(rows),2);self.assertTrue(all('result' in x for x in rows));self.assertEqual(proc.stderr,'')
