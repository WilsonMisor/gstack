import { appendFileSync, existsSync, mkdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { spawnSync } from 'child_process';
import { createHash } from 'crypto';

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

export function sha256Bytes(data: Uint8Array | string): string {
  return createHash('sha256').update(data).digest('hex');
}

export function sha256File(path: string): string {
  return sha256Bytes(readFileSync(path));
}

export function readJson<T = any>(path: string): T {
  return JSON.parse(readFileSync(path, 'utf8')) as T;
}

export function writeJsonAtomic(path: string, value: unknown): void {
  mkdirSync(dirname(path), { recursive: true });
  const tmp = `${path}.tmp-${process.pid}-${Date.now()}`;
  writeFileSync(tmp, `${JSON.stringify(value, null, 2)}\n`, { encoding: 'utf8', mode: 0o600 });
  try {
    renameSync(tmp, path);
  } catch (e) {
    if (existsSync(path) && statSync(path).isFile()) {
      rmSync(path);
      renameSync(tmp, path);
    } else {
      throw e;
    }
  }
}

export function appendJsonl(path: string, value: unknown): void {
  mkdirSync(dirname(path), { recursive: true });
  appendFileSync(path, `${JSON.stringify(value)}\n`, { encoding: 'utf8', mode: 0o600 });
}

export function git(args: string[], cwd?: string): { ok: boolean; stdout: string; stderr: string } {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8', timeout: 30000 });
  return {
    ok: r.status === 0,
    stdout: (r.stdout || '').trim(),
    stderr: (r.stderr || '').trim(),
  };
}

export function repoRoot(cwd = process.cwd()): string {
  const r = git(['rev-parse', '--show-toplevel'], cwd);
  if (!r.ok || !r.stdout) throw new Error(`not in a git repository: ${r.stderr || cwd}`);
  return resolve(r.stdout);
}

export function branchName(cwd = process.cwd()): string {
  const r = git(['branch', '--show-current'], cwd);
  return r.ok && r.stdout ? r.stdout : 'no-branch';
}

export function headSha(cwd = process.cwd()): string | null {
  const r = git(['rev-parse', 'HEAD'], cwd);
  return r.ok && r.stdout ? r.stdout : null;
}

export function workingTreeFingerprint(cwd = process.cwd()): string {
  const root = repoRoot(cwd);
  const parts: string[] = [];
  for (const args of [
    ['status', '--porcelain=v1', '-z'],
    ['diff', '--binary'],
    ['diff', '--cached', '--binary'],
  ]) {
    const r = git(args, root);
    if (!r.ok) throw new Error(`git ${args.join(' ')} failed: ${r.stderr}`);
    parts.push(r.stdout);
  }
  return sha256Bytes(parts.join('\n---\n'));
}

export function gstackStateRoot(): string {
  if (process.env.GSTACK_STATE_ROOT) return resolve(process.env.GSTACK_STATE_ROOT);
  if (process.env.GSTACK_HOME) return resolve(process.env.GSTACK_HOME);
  const home = process.env.HOME || process.env.USERPROFILE;
  if (!home) throw new Error('cannot resolve HOME/USERPROFILE for gstack state');
  return join(resolve(home), '.gstack');
}

export function projectSlug(cwd = process.cwd()): string {
  const root = repoRoot(cwd);
  const remote = git(['config', '--get', 'remote.origin.url'], root).stdout;
  const raw = remote || root;
  return raw
    .replace(/^.*[:/]([^/]+)\/([^/]+?)(?:\.git)?$/, '$1-$2')
    .replace(/[^A-Za-z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase() || 'project';
}

export function productionStateDir(cwd = process.cwd()): string {
  return join(gstackStateRoot(), 'projects', projectSlug(cwd), 'production');
}

export function isoNow(): string {
  return new Date().toISOString();
}

export function requireNonEmpty(value: unknown, label: string): void {
  const empty = value == null || value === '' || (Array.isArray(value) && value.length === 0);
  if (empty) throw new Error(`${label} is required`);
}

export function fail(message: string): never {
  console.error(`PREOS_BLOCKED: ${message}`);
  process.exit(2);
}
