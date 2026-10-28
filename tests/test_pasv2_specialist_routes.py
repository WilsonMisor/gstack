import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from pasv2_specialist_routes import route_specialists


class SpecialistRouteTests(unittest.TestCase):
    def test_high_assurance_routes_resolve_actual_skill_entrypoints(self):
        result=route_specialists({'money_movement':True,'personal_data':True,'tenant_model':'multi-tenant','profiles':['web','api'],'architecture':['queue','relational database']})
        self.assertEqual({r['skill'] for r in result['requests']},{'gstack-cso','gstack-review','gstack-qa','gstack-benchmark'})
        self.assertTrue(all((ROOT/r['entrypoint']).is_file() for r in result['requests']))
        self.assertTrue(all(r['execution_state']=='ROUTED_NOT_EXECUTED' for r in result['requests']))
        self.assertFalse(result['production_authorized'])

    def test_documentation_does_not_read_metadata_or_invoke_specialists(self):
        with tempfile.TemporaryDirectory() as temporary:
            result=route_specialists({'documentation_only':True},root=Path(temporary))
            self.assertEqual(result['requests'],[])
            self.assertEqual(result['metadata_files_read'],0)

    def test_missing_distribution_skill_blocks_routing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'integration').mkdir()
            shutil.copyfile(ROOT/'integration/pasv2-specialist-routes.json',root/'integration/pasv2-specialist-routes.json')
            (root/'CODEX-DISTRIBUTION.json').write_text(json.dumps({'skills':[]}))
            with self.assertRaisesRegex(ValueError,'absent from distribution'):
                route_specialists({'money_movement':True},root=root)


if __name__=='__main__': unittest.main()
