#!/usr/bin/env bun
import { lstatSync, readdirSync, readFileSync, statSync } from 'fs';
import { basename, join, relative, resolve } from 'path';
import { sha256File } from './lib';

export interface SourceEntry {
  path: string;
  type: 'file' | 'directory' | 'symlink' | 'zip-entry';
  size: number;
  mtime: string | null;
  sha256: string | null;
  blocked_reason?: string;
}

const EXECUTABLE_EXTENSIONS = new Set(['.exe','.dll','.com','.bat','.cmd','.ps1','.sh','.msi','.jar','.app','.scr','.vbs','.js','.mjs','.cjs','.py','.rb','.pl','.php']);
const MACRO_EXTENSIONS = new Set(['.docm','.xlsm','.pptm','.xlam']);

function ext(path: string): string {
  const i = path.lastIndexOf('.');
  return i >= 0 ? path.slice(i).toLowerCase() : '';
}

export function unsafeArchivePath(name: string): string | null {
  const normalized = name.replace(/\\/g, '/');
  if (!normalized || normalized.includes('\0')) return 'invalid archive entry name';
  if (normalized.startsWith('/') || /^[A-Za-z]:\//.test(normalized)) return 'absolute archive path';
  const parts = normalized.split('/');
  if (parts.some((p) => p === '..')) return 'path traversal';
  return null;
}

export function zipEntries(path: string): SourceEntry[] {
  const b = readFileSync(path);
  const sig = 0x02014b50;
  const out: SourceEntry[] = [];
  let i = 0;
  while (i + 46 <= b.length) {
    if (b.readUInt32LE(i) !== sig) { i++; continue; }
    const uncompressedSize = b.readUInt32LE(i + 24);
    const nameLen = b.readUInt16LE(i + 28);
    const extraLen = b.readUInt16LE(i + 30);
    const commentLen = b.readUInt16LE(i + 32);
    const externalAttrs = b.readUInt32LE(i + 38);
    const name = b.subarray(i + 46, i + 46 + nameLen).toString('utf8');
    const unixMode = (externalAttrs >>> 16) & 0xffff;
    const isSymlink = (unixMode & 0o170000) === 0o120000;
    const blocked = unsafeArchivePath(name) || (isSymlink ? 'symlink archive entry' : undefined);
    out.push({ path: name, type: 'zip-entry', size: uncompressedSize, mtime: null, sha256: null, ...(blocked ? { blocked_reason: blocked } : {}) });
    i += 46 + nameLen + extraLen + commentLen;
  }
  if (out.length === 0) throw new Error('ZIP central directory not found or archive unsupported/corrupt');
  return out;
}

export function inventory(input: string): { root: string; entries: SourceEntry[]; warnings: string[]; blocked: boolean } {
  const root = resolve(input);
  const entries: SourceEntry[] = [];
  const warnings: string[] = [];

  function visit(p: string): void {
    const st = lstatSync(p);
    const rel = relative(root, p) || basename(root);
    if (st.isSymbolicLink()) {
      entries.push({ path: rel, type: 'symlink', size: 0, mtime: st.mtime.toISOString(), sha256: null, blocked_reason: 'source symlink is not followed during intake' });
      return;
    }
    if (st.isDirectory()) {
      entries.push({ path: rel, type: 'directory', size: 0, mtime: st.mtime.toISOString(), sha256: null });
      for (const name of readdirSync(p)) visit(join(p, name));
      return;
    }
    if (!st.isFile()) return;
    const e = ext(p);
    let blocked_reason: string | undefined;
    if (EXECUTABLE_EXTENSIONS.has(e)) blocked_reason = 'executable/script source: inventory only; do not execute for inspection';
    if (MACRO_EXTENSIONS.has(e)) blocked_reason = 'macro-enabled document: inventory only; do not execute macros';
    entries.push({ path: rel, type: 'file', size: st.size, mtime: st.mtime.toISOString(), sha256: sha256File(p), ...(blocked_reason ? { blocked_reason } : {}) });
    if (e === '.zip') {
      const z = zipEntries(p);
      for (const ze of z) entries.push({ ...ze, path: `${rel}!/${ze.path}` });
    }
  }

  if (!statSync(root).isDirectory() && ext(root) === '.zip') {
    const st = statSync(root);
    entries.push({ path: basename(root), type: 'file', size: st.size, mtime: st.mtime.toISOString(), sha256: sha256File(root) });
    for (const ze of zipEntries(root)) entries.push({ ...ze, path: `${basename(root)}!/${ze.path}` });
  } else {
    visit(root);
  }
  const archiveBlocks = entries.filter((e) => e.type === 'zip-entry' && e.blocked_reason);
  if (archiveBlocks.length) warnings.push(`${archiveBlocks.length} unsafe ZIP entries detected; archive extraction must be blocked`);
  const totalBytes = entries.reduce((n, e) => n + (e.type === 'file' ? e.size : 0), 0);
  if (entries.length > 10000) warnings.push('large source package: more than 10,000 entries');
  if (totalBytes > 2 * 1024 * 1024 * 1024) warnings.push('large source package: more than 2 GiB');
  return { root, entries, warnings, blocked: archiveBlocks.length > 0 };
}

if (import.meta.main) {
  const input = process.argv[2];
  if (!input) throw new Error('usage: safe-source-inventory.ts <folder-or-zip>');
  const result = inventory(input);
  console.log(JSON.stringify(result, null, 2));
  if (result.blocked) process.exit(2);
}
