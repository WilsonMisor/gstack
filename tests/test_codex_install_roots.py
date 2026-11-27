import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('materializer',ROOT/'scripts/build_codex_distribution.py')
materializer=importlib.util.module_from_spec(spec);spec.loader.exec_module(materializer)

class CodexInstallRootTests(unittest.TestCase):
    def test_installed_commands_resolve_default_and_custom_roots_with_spaces(self):
        bash=Path('C:/Program Files/Git/bin/bash.exe') if os.name=='nt' else Path(shutil.which('bash'))
        with tempfile.TemporaryDirectory(prefix='codex root ') as td:
            root=Path(td);target=root/'distribution';target.mkdir();skill=target/'SKILL.md'
            skill.write_text(materializer.LEGACY_ROOT_ASSIGNMENT+'\n',encoding='utf-8')
            materializer.bind_codex_runtime_root(target)
            for values,expected in [({'HOME':root.as_posix()},root/'.codex/skills/gstack'),({'CODEX_HOME':(root/'custom home').as_posix()},root/'custom home/skills/gstack'),({'CODEX_SKILL_ROOT':(root/'custom skills').as_posix()},root/'custom skills/gstack'),({'CODEX_SKILLS_HOME':(root/'legacy setting').as_posix()},root/'legacy setting/gstack')]:
                (expected/'bin').mkdir(parents=True,exist_ok=True)
                env={k:v for k,v in os.environ.items() if k not in ('CODEX_HOME','CODEX_SKILL_ROOT','CODEX_SKILLS_HOME')};env.update(values)
                script=skill.read_text()+'test -d "$GSTACK_ROOT/bin" || exit 3\ncd "$GSTACK_ROOT"\n'+('pwd -W' if os.name=='nt' else 'pwd -P')+'\n'
                proc=subprocess.run([str(bash),'--noprofile','--norc','-c',script],env=env,capture_output=True,text=True)
                self.assertEqual(proc.returncode,0,proc.stderr);self.assertEqual(proc.stdout.strip(),expected.resolve().as_posix())

    def test_global_binding_is_idempotent_and_preserves_project_override(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);path=root/'SKILL.md';override='[ -n "$_ROOT" ] && GSTACK_ROOT="$_ROOT/.agents/skills/gstack"'
            path.write_text(materializer.LEGACY_ROOT_ASSIGNMENT+'\n'+override+'\n')
            materializer.bind_codex_runtime_root(root);first=path.read_bytes();materializer.bind_codex_runtime_root(root)
            self.assertEqual(path.read_bytes(),first);self.assertIn(override,path.read_text())

    def test_distribution_rejects_unbound_global_runtime_root(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'SKILL.md').write_text(materializer.LEGACY_ROOT_ASSIGNMENT)
            with self.assertRaisesRegex(materializer.DistributionError,'runtime root'):
                materializer.validate_distribution(root,{'skills':[]})

if __name__=='__main__':unittest.main()
