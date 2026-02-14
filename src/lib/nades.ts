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

// Inline SVG icons for throw techniques (monochrome, use currentColor)
// Mouse icons: rounded rect outline with vertical divider, left or right half filled
const ICON_MOUSE_LEFT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="2" width="16" height="20" rx="8" /><line x1="12" y1="2" x2="12" y2="12" /><path d="M4.54 5.56A8 8 0 0 1 12 2v10H4V8a8 8 0 0 1 .54-2.44Z" fill="currentColor" stroke="none" /></svg>';
const ICON_MOUSE_RIGHT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="2" width="16" height="20" rx="8" /><line x1="12" y1="2" x2="12" y2="12" /><path d="M19.46 5.56A8 8 0 0 0 12 2v10h8V8a8 8 0 0 0-.54-2.44Z" fill="currentColor" stroke="none" /></svg>';
const ICON_MOUSE_BOTH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="2" width="16" height="20" rx="8" /><line x1="12" y1="2" x2="12" y2="12" /><path d="M4.54 5.56A8 8 0 0 1 12 2v10H4V8a8 8 0 0 1 .54-2.44Z" fill="currentColor" stroke="none" /><path d="M19.46 5.56A8 8 0 0 0 12 2v10h8V8a8 8 0 0 0-.54-2.44Z" fill="currentColor" stroke="none" /></svg>';
// Jump icon: person in mid-air with arms/legs spread
const ICON_JUMP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="4" r="2" fill="currentColor" /><path d="M7 11.5l3-2 2 3 2-3 3 2" /><path d="M8 20l2.5-5h3L16 20" /><line x1="10.5" y1="15" x2="9" y2="17" /><line x1="13.5" y1="15" x2="15" y2="17" /></svg>';
// Running person icon
const ICON_RUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><circle cx="13" cy="4" r="2" fill="currentColor" /><path d="M7 21l3-7 2.5 2" /><path d="M16 21l-2-5-4-2 2-4 4 1 2 3" /><path d="M6 12l4 2" /></svg>';
// Community badge: two people (users icon, similar to Lucide "users")
const ICON_COMMUNITY = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>';

export const TECHNIQUE_ICONS: Record<string, string> = {
  left: ICON_MOUSE_LEFT,
  right: ICON_MOUSE_RIGHT,
  left_jump: ICON_JUMP,
  right_jump: ICON_JUMP,
  left_right: ICON_MOUSE_BOTH,
  run_left: ICON_RUN,
  run_right: ICON_RUN,
  run_left_jump: ICON_RUN,
};

export const COMMUNITY_ICON = ICON_COMMUNITY;

export function isCommunityNade(nade: Nade): boolean {
  return !nade.source_url.includes('csnades.gg');
}

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
