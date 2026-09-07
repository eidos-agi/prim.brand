from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from jsonschema import Draft202012Validator
from brandkit.io import Invalid,load,save,sha,digest,face,local,files
from brandkit.schema import SCHEMA,APPROVAL_SCHEMA
from brandkit.tokens import resolve,resolve_sets,compiled,validate_value,css_value
from brandkit.validate import validate,asset_digest,css_scan
from brandkit.operations import compile_tokens,inventory,select,release,verify_release,bundle,diff,migrate,preview
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixtures',ROOT/'scripts/build_examples.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

class KitTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.pack=self.base/'pack';self.ident=fixture.comprehensive(self.pack)
    def tearDown(self):self.temp.cleanup()
    def write(self):save(self.pack/'identity.json',self.ident)
    def report(self):self.write();return validate(self.pack)
    def broken(self):self.assertFalse(self.report()['passed'])
    def test_truncated_png_rejected(self):
        import struct
        p=self.pack/'assets/broken.png';p.write_bytes(b'\x89PNG\r\n\x1a\n'+struct.pack('>I',13)+b'IHDR'+struct.pack('>II',10,10))
        a=copy.deepcopy(self.ident['assets'][0]);a.update(id='broken:png',path='assets/broken.png',sha256=sha(p),media_type='image/png',representation='raster',editable='none');a.pop('view_box',None);self.ident['assets'].append(a);self.broken()
    def test_schema_is_valid(self):Draft202012Validator.check_schema(SCHEMA);Draft202012Validator.check_schema(APPROVAL_SCHEMA)
    def test_comprehensive(self):self.assertTrue(self.report()['passed']);self.assertFalse(self.report()['ready_for_use'])
    def test_minimal_without_font_or_blocks(self):
        p=self.base/'minimal';fixture.minimal(p);self.assertTrue(validate(p)['passed'])
    def test_missing_face(self):(self.pack/'index.md').unlink();self.broken()
    def test_wrong_face_hidden_in_example(self):
        (self.pack/'index.md').write_text('---\nprofile: something-else\ntype: kit\n---\nprofile: brand\n');self.broken()
    def test_duplicate_yaml(self):
        (self.pack/'index.md').write_text('---\nprofile: brand\nprofile: obf\ntype: kit\n---\n');self.broken()
    def test_yaml_alias_rejected(self):
        (self.pack/'index.md').write_text('---\nprofile: brand\ntype: kit\na: &a [1]\nb: *a\n---\n');self.broken()
    def test_duplicate_json(self):
        (self.pack/'identity.json').write_text('{"id":1,"id":2}');self.assertFalse(validate(self.pack)['passed'])
    def test_nonfinite_json(self):
        (self.pack/'identity.json').write_text('{"value": NaN}');self.assertFalse(validate(self.pack)['passed'])
    def test_missing_log(self):(self.pack/'log.md').unlink();self.broken()
    def test_version_mismatch(self):self.ident['brand_version']='99.0.0';self.broken()
    def test_unknown_required_capability(self):
        self.ident['capabilities'].append('vendor:unknown');self.ident['required_capabilities'].append('vendor:unknown');self.ident['extensions']={'vendor:unknown':{}};self.broken()
    def test_unknown_optional_warns(self):
        self.ident['capabilities'].append('vendor:unknown');self.ident['extensions']={'vendor:unknown':{}};self.assertTrue(self.report()['passed'])
    def test_declared_missing_capability_data(self):del self.ident['sound'];self.broken()
    def test_duplicate_asset_id(self):self.ident['assets'].append(copy.deepcopy(self.ident['assets'][0]));self.broken()
    def test_asset_hash(self):self.ident['assets'][0]['sha256']='0'*64;self.broken()
    def test_missing_asset(self):(self.pack/'assets/mark.svg').unlink();self.broken()
    def test_unsafe_path(self):self.ident['assets'][0]['path']='../outside';self.broken()
    def test_windows_path(self):self.ident['assets'][0]['path']='C:\\Windows\\test';self.broken()
    def test_symlink(self):
        (self.pack/'assets/mark.svg').unlink();(self.base/'outside.svg').write_text('x');(self.pack/'assets/mark.svg').symlink_to(self.base/'outside.svg');self.broken()
    def test_directory_symlink(self):(self.pack/'link').symlink_to(self.base,target_is_directory=True);self.broken()
    def test_planned_required(self):self.ident['assets'][0]['availability']='planned';self.broken()
    def test_missing_optional_reported(self):
        self.ident['assets'][1]['availability']='missing';self.assertTrue(self.report()['passed']);self.assertEqual(self.report()['dimensions']['completeness'],'warnings')
    def test_not_a_vector(self):
        a=self.ident['assets'][0];p=self.pack/a['path'];p.write_text('<svg viewBox="0 0 2 2"><image/></svg>');a['sha256']=sha(p);self.broken()
    def test_active_svg(self):
        a=self.ident['assets'][0];p=self.pack/a['path'];p.write_text('<svg viewBox="0 0 2 2"><script/></svg>');a['sha256']=sha(p);self.broken()
    def test_svg_external_ref(self):
        a=self.ident['assets'][0];p=self.pack/a['path'];p.write_text('<svg viewBox="0 0 2 2"><use href="https://example.invalid/a.svg"/></svg>');a['sha256']=sha(p);self.broken()
    def test_svg_zero_viewbox(self):
        a=self.ident['assets'][0];p=self.pack/a['path'];p.write_text('<svg viewBox="0 0 0 2"/>');a['sha256']=sha(p);self.broken()
    def test_stale_lineage(self):self.ident['assets'][1]['derived_from'][0]['sha256']='0'*64;self.broken()
    def test_lineage_cycle(self):
        self.ident['assets'][0]['derived_from']=[{'id':self.ident['assets'][1]['id'],'sha256':self.ident['assets'][1]['sha256']}];self.broken()
    def test_reconstruction_requires_review(self):self.ident['recipes'][0]['operation']='reconstruct';self.broken()
    def test_generation_not_repeatable(self):
        self.ident['recipes'][0].update(operation='generate',requires_review=True);self.broken()
    def test_missing_deliverable(self):self.ident['deliverables'][0]['asset_id']='no-such-asset';self.broken()
    def test_font_strategy_not_empty_bundled(self):
        self.ident['typography'][0].update(strategy='bundled',asset_ids=[],license='x',license_path='x');self.broken()
    def test_missing_tokens(self):(self.pack/'tokens/dtcg.json').unlink();self.broken()
    def test_missing_css(self):(self.pack/'kit.css').unlink();self.broken()
    def test_css_drift(self):(self.pack/'kit.css').write_text(':root{}');self.broken()
    def test_css_unknown_token(self):(self.pack/'blocks/hero/block.css').write_text('.a{color:var(--invented)}');self.broken()
    def test_css_literals(self):(self.pack/'blocks/hero/block.css').write_text('.a{color:#fff;padding:12px}');self.broken()
    def test_css_network(self):(self.pack/'blocks/hero/block.css').write_text('@import "https://example.invalid/x.css";');self.broken()
    def test_html_script(self):(self.pack/'blocks/hero/block.html').write_text('<script>alert(1)</script>');self.broken()
    def test_html_handler(self):(self.pack/'blocks/hero/block.html').write_text('<div onclick="alert(1)">x</div>');self.broken()
    def test_html_external(self):(self.pack/'blocks/hero/block.html').write_text('<img src="https://example.invalid/x">');self.broken()
    def test_motion_missing_fallback(self):self.ident['motion'][0]['reduced_motion_asset']='missing';self.broken()
    def test_sound_autoplay(self):self.ident['sound'][0]['autoplay']=True;self.broken()
    def test_sound_duration(self):self.ident['sound'][0]['duration_ms']=999;self.broken()
    def test_locale_cycle(self):self.ident['localization'][0]['fallback_locale']='fr';self.broken()
    def test_locale_unknown_font(self):self.ident['localization'][0]['typeface_ids']=['missing'];self.broken()
    def test_self_relationship(self):self.ident['relationships'][0]['brand_id']=self.ident['id'];self.broken()
    def test_no_global_house_color(self):self.assertTrue(self.report()['passed'])
    def test_house_color_rule_scoped(self):
        self.ident['rules'].append({'id':'rule:color','kind':'forbidden-color','severity':'error','paths':['assets/mark.svg'],'value':'#6c8aff'});self.broken()
    def test_contrast_failure(self):self.ident['rules'][0]['foreground']='#000000';self.broken()
    def test_self_approval_not_authority(self):self.ident['assets'][0]['approval']='approved';self.assertFalse(self.report()['ready_for_use'])
    def trust_decision(self,scope='asset',decision='approve'):
        data=load(self.pack/'approvals.json');d=data['decisions'][0];d['scope']=scope;d['decision']=decision
        d['subjects'][0]['record_sha256']=asset_digest(self.ident['assets'][0]);save(self.pack/'approvals.json',data)
        trust={'version':'0.2.0','trusted_decisions':[{'sha256':digest(d),'principal':d['principal'],'scopes':[scope]}],'revoked':[]};save(self.base/'trust.json',trust);self.write();return self.base/'trust.json'
    def test_external_trust(self):
        trust=self.trust_decision();self.assertTrue(validate(self.pack,trust)['ready_for_use'])
    def test_reference_does_not_approve_asset(self):
        trust=self.trust_decision('reference');self.assertFalse(validate(self.pack,trust)['ready_for_use'])
    def test_rejection(self):
        trust=self.trust_decision('asset','reject');self.assertFalse(validate(self.pack,trust)['ready_for_use'])
    def test_revocation(self):
        trust=self.trust_decision();t=load(trust);t['revoked']=[t['trusted_decisions'][0]['sha256']];save(trust,t);self.assertFalse(validate(self.pack,trust)['ready_for_use'])
    def test_embedded_trust_refused(self):
        trust=self.trust_decision();shutil.copyfile(trust,self.pack/'trust.json');self.assertFalse(validate(self.pack,self.pack/'trust.json')['passed'])
    def test_changed_usage_invalidates_approval(self):
        trust=self.trust_decision();self.ident['assets'][0]['constraints']={'min_px':500};self.write();self.assertFalse(validate(self.pack,trust)['passed'])
    def test_selection(self):self.assertEqual(select(self.pack,{'id':'mark:primary'})['id'],'mark:primary')
    def test_selection_ambiguous(self):
        with self.assertRaises(Invalid):select(self.pack,{'media_type':'image/svg+xml'})
    def test_selection_not_approved(self):
        with self.assertRaises(Invalid):select(self.pack,{'id':'mark:primary','approved':True})
    def test_release_no_false_approval(self):
        out=self.base/'release.json';release(self.pack,out);result=verify_release(self.pack,out);self.assertTrue(result['integrity_matches']);self.assertFalse(result['authorized'])
    def test_release_detects_change(self):
        out=self.base/'release.json';release(self.pack,out);(self.pack/'log.md').write_text('change');self.assertFalse(verify_release(self.pack,out)['integrity_matches'])
    def test_release_trusted(self):
        out=self.base/'release.json';manifest=release(self.pack,out);data=load(self.pack/'approvals.json');d=data['decisions'][0];d.pop('subjects');d.update(scope='release',release_sha256=manifest['sha256']);save(self.pack/'approvals.json',data)
        trust=self.base/'trust.json';save(trust,{'version':'0.2.0','trusted_decisions':[{'sha256':digest(d),'principal':d['principal'],'scopes':['release']}],'revoked':[]})
        self.assertTrue(verify_release(self.pack,out,trust)['ready_for_use'])
    def test_bundle_deterministic(self):
        a=bundle(self.pack,self.base/'a.zip');b=bundle(self.pack,self.base/'b.zip');self.assertEqual(a['sha256'],b['sha256'])
    def test_bundle_refuses_fonts(self):
        (self.pack/'private.ttf').write_bytes(b'not distributed')
        with self.assertRaises(Invalid):bundle(self.pack,self.base/'a.zip')
    def test_output_no_overwrite(self):
        with self.assertRaises(Invalid):preview(self.pack,self.pack/'index.md')
    def test_preview_inert(self):
        out=self.base/'preview.html';preview(self.pack,out);text=out.read_text();self.assertNotIn('<svg',text);self.assertNotIn('<script',text)
    def test_diff_marks_rebrand(self):
        other=self.base/'other';shutil.copytree(self.pack,other);i=load(other/'identity.json');i['name']='Other';save(other/'identity.json',i);self.assertTrue(diff(self.pack,other)['changes'])
    def test_legacy_migration_preserves_logo(self):
        old=self.base/'old';old.mkdir();(old/'index.md').write_text('---\nprofile: brand\ntype: kit\nbrand_version: "0.1.0"\ntitle: "Old"\n---\n');shutil.copytree(self.pack/'assets',old/'assets')
        source={'brand_version':'0.1.0','brand':{'id':'brand:old','display_name':'Old'},'logo':[{'id':'logo:old','path':'assets/mark.svg','sha256':sha(old/'assets/mark.svg')}],'typefaces':[]}
        save(old/'identity.json',source);before=sha(old/'identity.json');dest=self.base/'migrated';migrate(old,dest)
        self.assertEqual(sha(old/'identity.json'),before);self.assertEqual(sha(old/'assets/mark.svg'),sha(dest/'assets/mark.svg'));self.assertTrue(validate(dest)['passed'])

class TokenTests(unittest.TestCase):
    def test_alias_and_inheritance(self):
        d={'color':{'$type':'color','a':{'$value':{'colorSpace':'srgb','components':[1,0,0]}},'b':{'$value':'{color.a}'}}};self.assertEqual(resolve(d)['color.b']['$type'],'color')
    def test_alias_type_mismatch(self):
        with self.assertRaises(Invalid):resolve({'a':{'$type':'number','$value':1},'b':{'$type':'color','$value':'{a}'}})
    def test_alias_cycle(self):
        with self.assertRaises(Invalid):resolve({'a':{'$type':'number','$value':'{b}'},'b':{'$type':'number','$value':'{a}'}})
    def test_missing_alias(self):
        with self.assertRaises(Invalid):resolve({'a':{'$type':'number','$value':'{no}'}})
    def test_json_pointer(self):
        self.assertEqual(resolve({'a':{'$type':'number','$value':1},'b':{'$type':'number','$value':{'$ref':'#/a/$value'}}})['b']['$value'],1)
    def test_pointer_cycle(self):
        with self.assertRaises(Invalid):resolve({'a':{'$type':'number','$value':{'$ref':'#/a/$value'}}})
    def test_group_extension(self):
        d={'base':{'$type':'number','a':{'$value':1}},'other':{'$extends':'{base}','b':{'$value':2}}};self.assertEqual(resolve(d)['other.a']['$value'],1)
    def test_group_cycle(self):
        with self.assertRaises(Invalid):resolve({'a':{'$extends':'{b}'},'b':{'$extends':'{a}'}})
    def test_bad_token_name(self):
        with self.assertRaises(Invalid):resolve({'a.b':{'$type':'number','$value':1}})
    def test_old_hex_not_2025_color(self):
        with self.assertRaises(Invalid):resolve({'a':{'$type':'color','$value':'#ffffff'}})
    def test_invalid_duration(self):
        with self.assertRaises(Invalid):validate_value('duration',{'value':-1,'unit':'ms'})
    def test_invalid_dimension_unit(self):
        with self.assertRaises(Invalid):validate_value('dimension',{'value':1,'unit':'em'})
    def test_bezier_bounds(self):
        with self.assertRaises(Invalid):validate_value('cubicBezier',[2,0,1,1])
    def test_gradient(self):
        validate_value('gradient',[{'color':{'colorSpace':'display-p3','components':[1,0,0]},'position':0}])
    def test_css_unsupported_fails(self):
        with self.assertRaises(Invalid):css_value('strokeStyle',{'dashArray':[{'value':1,'unit':'px'}],'lineCap':'butt'})
    def test_resolver_context(self):
        with tempfile.TemporaryDirectory() as d:
            pack=Path(d);i=fixture.comprehensive(pack);settings=i['tokens'];light=resolve(resolve_sets(pack,settings['resolver'],{'theme':'light'}));dark=resolve(resolve_sets(pack,settings['resolver'],{'theme':'dark'}));self.assertNotEqual(light['text'],dark['text'])
    def test_resolver_bad_input(self):
        with tempfile.TemporaryDirectory() as d:
            pack=Path(d);fixture.comprehensive(pack)
            with self.assertRaises(Invalid):resolve_sets(pack,'tokens/resolver.json',{'unknown':'x'})
    def test_resolver_cycle(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);save(p/'resolver.json',{'sets':{'a':{'sources':[{'$ref':'#/sets/a'}]}},'resolutionOrder':[{'$ref':'#/sets/a'}]})
            with self.assertRaises(Invalid):resolve_sets(p,'resolver.json',{})
    def test_resolver_escape(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);save(p/'resolver.json',{'sets':{'a':{'sources':[{'$ref':'../private.json'}]}},'resolutionOrder':[{'$ref':'#/sets/a'}]})
            with self.assertRaises(Invalid):resolve_sets(p,'resolver.json',{})

if __name__=='__main__':unittest.main()
