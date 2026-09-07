import copy
from pathlib import Path
import shutil
import tempfile
import unittest
from brandkit.io import Invalid,sha
from brandkit.export import export_asset
from brandkit.operations import diff
from test_brand import fixture

class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.pack=self.base/'pack';fixture.minimal(self.pack)
    def tearDown(self):self.temp.cleanup()
    def test_copy_exact(self):
        record=export_asset(self.pack,'mark:primary',self.base/'copy');self.assertEqual(record['sha256'],sha(self.pack/'assets/mark.svg'));self.assertEqual(record['approval'],'candidate')
    def test_raster_export(self):
        from PIL import Image
        record=export_asset(self.pack,'mark:primary',self.base/'png',64);self.assertEqual(record['operation'],'rasterize')
        with Image.open(self.base/'png/asset.png') as im:self.assertEqual(im.size,(64,64))
    def test_bounded(self):
        with self.assertRaises(Invalid):export_asset(self.pack,'mark:primary',self.base/'bad',100000)
    def test_source_unchanged(self):
        before=sha(self.pack/'identity.json');export_asset(self.pack,'mark:primary',self.base/'copy');self.assertEqual(before,sha(self.pack/'identity.json'))
    def test_log_edit_not_append(self):
        other=self.base/'other';shutil.copytree(self.pack,other);(other/'log.md').write_text('rewrite');self.assertFalse(diff(self.pack,other)['log_append_only'])
