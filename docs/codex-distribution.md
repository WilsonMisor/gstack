# Codex Distribution

This repository uses a source-based Codex distribution for gstack.

`CODEX-DISTRIBUTION.json` is the schema-valid manifest consumed by the governed three-repository installer. The manifest declares generated skill folders under `codex-distribution/`, but that tree is not canonical Git source and is not committed.

## Materialization

Run this from the repository root:

```bash
python scripts/build_codex_distribution.py
```

The materializer regenerates Codex skill docs, compiles runtime binaries with Bun, builds the Node-compatible browser server bundle, writes commit `.version` files, and creates `codex-distribution/` locally. The `browse` CLI executable is compiled from a scrubbed intermediate bundle so the output is stable across checkout paths.

Use this validation in CI or before installation:

```bash
python scripts/build_codex_distribution.py --check
```

`--check` materializes into a temporary tree, validates every declared skill, verifies required runtime artifacts, and fails if `codex-distribution/` is tracked or mapped to Git LFS.

## Version Control Policy

The canonical source remains `WilsonMisor/gstack` at a Git commit. Source files, templates, scripts, manifests, tests, docs, schemas, and compatibility metadata are version-controlled. Generated runtime binaries and generated distribution output are reconstructed locally from source and are ignored by Git.

This avoids requiring new Git LFS uploads to the public fork for artifacts that can be deterministically rebuilt.

## Provenance And Receipt

Each materialized distribution writes `.codex-distribution-provenance.json` at the distribution root and inside the installed `gstack` skill payload. It records the source commit, materializer version and hash, build contract hash, compatibility versions, runtime artifact hashes, and generated payload hash.

After the governed package installer runs, augment and verify the framework receipt:

```bash
python scripts/build_codex_distribution.py --augment-receipt "$HOME/.codex/framework-installations/wilson-production-framework.json"
```

The receipt remains the machine-readable installation authority and records generated runtime hashes alongside installed runtime hashes.