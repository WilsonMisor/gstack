import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('compatibility',ROOT/'scripts/validate-pasv2-compatibility.py')
compatibility=importlib.util.module_from_spec(spec);spec.loader.exec_module(compatibility)


class CompatibilityContractTests(unittest.TestCase):
    def test_integrated_main_requires_compatible_ancestry(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo=Path(temporary)
            def git(*args):
                return subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True,text=True).stdout.strip()
            git('init','-b','main');git('config','user.email','fixture@example.invalid');git('config','user.name','Fixture')
            (repo/'content').write_text('base');git('add','.');git('commit','-m','base')
            expected='pasv2/final-residual-remediation'
            with self.assertRaises(SystemExit):compatibility.validate_checkout_ref(repo,expected,'blueprint')
            git('checkout','-b',expected)
            (repo/'content').write_text('candidate');git('add','.');git('commit','-m','candidate')
            compatibility.validate_checkout_ref(repo,expected,'blueprint')
            git('checkout','main')
            with self.assertRaises(SystemExit):compatibility.validate_checkout_ref(repo,expected,'blueprint')
            git('merge','--no-ff',expected,'-m','integrated fixture')
            compatibility.validate_checkout_ref(repo,expected,'blueprint')
            git('checkout','-b','unapproved-label')
            with self.assertRaises(SystemExit):compatibility.validate_checkout_ref(repo,expected,'blueprint')

    def test_all_actual_checkouts_share_version_and_resolvable_interfaces(self):
        manifest=compatibility.validate_static()
        results=compatibility.validate_local_checkouts(manifest,ROOT.parent/'wed_dev_skill',ROOT.parent/'PREOS',ROOT)
        self.assertEqual(len(results),3)
        self.assertEqual({r['compatibility_version'] for r in results},{compatibility.CONTRACT_VERSION})
        self.assertTrue(all(len(r['head'])==40 and len(r['tree'])==40 for r in results))

    def test_wrong_version_missing_interface_and_closed_authority_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo=Path(temporary)
            subprocess.run(['git','init'],cwd=repo,check=True,capture_output=True)
            subprocess.run(['git','config','user.email','fixture@example.invalid'],cwd=repo,check=True)
            subprocess.run(['git','config','user.name','Fixture'],cwd=repo,check=True)
            (repo/'module.py').write_text('def actual_interface():\n    return 1\n')
            subprocess.run(['git','add','module.py'],cwd=repo,check=True,capture_output=True)
            subprocess.run(['git','commit','-m','Fixture'],cwd=repo,check=True,capture_output=True)
            for mutation in ('version','symbol','gate'):
                contract={'component':'gstack','compatibility_version':compatibility.CONTRACT_VERSION,
                          'authority_boundary':{gate:'OPEN' for gate in compatibility.HUMAN_GATES},
                          'interfaces':['module.py::actual_interface']}
                if mutation=='version':contract['compatibility_version']='obsolete'
                if mutation=='symbol':contract['interfaces']=['module.py::missing_interface']
                if mutation=='gate':contract['authority_boundary']['PRODUCTION_RELEASE_AUTHORITY']='CLOSED'
                (repo/'PASV2-CONTRACT.json').write_text(json.dumps(contract))
                with self.assertRaises(SystemExit,msg=mutation):
                    compatibility.validate_repo(repo,[],'gstack')


if __name__=='__main__': unittest.main()
