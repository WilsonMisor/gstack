#!/usr/bin/env python3
"""Resolve governed specialist requests to actual installed-distribution skills."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def route_specialists(contract,*,root=ROOT):
    root=Path(root).resolve()
    if contract.get('documentation_only') is True:
        return {'requests':[],'metadata_files_read':0,'production_authorized':False}
    metadata=(root/'integration/pasv2-specialist-routes.json').read_bytes()
    rules=json.loads(metadata)
    if rules.get('schema_version')!='pasv2-specialist-routes-v1':
        raise ValueError('unsupported specialist routing contract')
    manifest=json.loads((root/'CODEX-DISTRIBUTION.json').read_text(encoding='utf-8'))
    skills={s['name']:s for s in manifest['skills']}
    requests=[]
    for rule in rules['routes']:
        matches=any(contract.get(k) is True for k in rule.get('any_true',[]))
        matches=matches or any(contract.get(k)==v for k,v in rule.get('any_equal',{}).items())
        matches=matches or bool(set(contract.get('profiles',[])) & set(rule.get('any_profiles',[])))
        matches=matches or bool(set(contract.get('architecture',[])) & set(rule.get('any_architecture',[])))
        if not matches: continue
        short=rule['skill'].removeprefix('gstack-')
        if short not in skills:
            raise ValueError('requested specialist is absent from distribution manifest: '+rule['skill'])
        path=(root/skills[short]['source_path']/'SKILL.md').resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError('specialist skill entry point does not resolve')
        requests.append({'skill':rule['skill'],'entrypoint':path.relative_to(root).as_posix(),
                         'entrypoint_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                         'required_findings':rule['required_findings'],'execution_state':'ROUTED_NOT_EXECUTED',
                         'return_to':'PREOS evidence and gate evaluation','production_authorized':False})
    return {'requests':requests,'metadata_files_read':2,'routing_sha256':hashlib.sha256(metadata).hexdigest(),
            'authority':rules['authority'],'production_authorized':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('contract',type=Path)
    args=parser.parse_args();print(json.dumps(route_specialists(json.loads(args.contract.read_text())),indent=2))


if __name__=='__main__': main()
