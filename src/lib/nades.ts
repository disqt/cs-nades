import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export interface Nade {
  slug: string;
  map: string;
  team: string;
  type: string;
  titleFrom: string;
  titleTo: string;
  technique: string;
  movement: string;
  console: string;
  asset_id: string;
  video_url: string;
  lineup_url: string;
  source_url: string;
  captions: string[];
}

const MAPS_ORDER = ['mirage', 'dust2', 'inferno', 'overpass', 'ancient', 'anubis', 'nuke'];

export const TECHNIQUE_LABELS: Record<string, string> = {
  left: 'Left Click',
  right: 'Right Click',
  left_jump: 'Jump Throw',
  right_jump: 'Right + Jump',
  left_right: 'Left + Right',
  run_left: 'Run + Left',
  run_right: 'Run + Right',
  run_left_jump: 'Run + Jump',
};
const DATA_DIR = import.meta.env.NADES_DATA_DIR || process.env.NADES_DATA_DIR || 'public/data';

let _cache: Nade[] | null = null;

export function loadNades(): Nade[] {
  if (_cache) return _cache;
  const raw = readFileSync(join(DATA_DIR, 'nades.json'), 'utf-8');
  _cache = JSON.parse(raw) as Nade[];
  return _cache;
}

export function invalidateCache(): void {
  _cache = null;
}

export function getMapsPresent(nades: Nade[]): string[] {
  const maps = [...new Set(nades.map(n => n.map))];
  return maps.sort((a, b) =>
    (MAPS_ORDER.indexOf(a) ?? 99) - (MAPS_ORDER.indexOf(b) ?? 99)
  );
}

// Seeded shuffle (same as Python version: seed by count, stable until new nades added)
export function seededShuffle<T>(arr: T[], seed: number): T[] {
  const result = [...arr];
  let s = seed;
  for (let i = result.length - 1; i > 0; i--) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const j = s % (i + 1);
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
