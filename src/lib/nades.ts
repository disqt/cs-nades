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

// Iconoir icons (MIT license, https://iconoir.com)
const ICON_MOUSE_LEFT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path d="M20 10V14C20 18.4183 16.4183 22 12 22C7.58172 22 4 18.4183 4 14V9C4 5.13401 7.13401 2 11 2H12C16.4183 2 20 5.58172 20 10Z" stroke-linecap="round"/><path d="M12 2V8.4C12 8.73137 11.7314 9 11.4 9H4" stroke-linecap="round"/></svg>';
const ICON_MOUSE_RIGHT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path d="M4 10V14C4 18.4183 7.58172 22 12 22C16.4183 22 20 18.4183 20 14V9C20 5.13401 16.866 2 13 2H12C7.58172 2 4 5.58172 4 10Z" stroke-linecap="round"/><path d="M12 2V8.4C12 8.73137 12.2686 9 12.6 9H20" stroke-linecap="round"/></svg>';
const ICON_MOUSE_BOTH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path d="M12 2V2C16.4183 2 20 5.58172 20 10V14C20 18.4183 16.4183 22 12 22V22C7.58172 22 4 18.4183 4 14V10C4 5.58172 7.58172 2 12 2V2ZM12 2V9" stroke-linecap="round"/></svg>';
const ICON_JUMP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path d="M6 7C4.89543 7 4 6.10457 4 5C4 3.89543 4.89543 3 6 3C7.10457 3 8 3.89543 8 5C8 6.10457 7.10457 7 6 7Z" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 15.5C18 14.5 15.5 15 13 20C12.5 17 11 12.5 9.5 10" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const ICON_RUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path d="M15 7C16.1046 7 17 6.10457 17 5C17 3.89543 16.1046 3 15 3C13.8954 3 13 3.89543 13 5C13 6.10457 13.8954 7 15 7Z" stroke-linecap="round" stroke-linejoin="round"/><path d="M12.6133 8.26691L9.30505 12.4021L13.4403 16.5374L11.3727 21.0861" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.4104 9.5075L9.79728 6.19931L12.6132 8.26692L15.508 11.5752H19.2297" stroke-linecap="round" stroke-linejoin="round"/><path d="M8.89152 15.7103L7.65095 16.5374H4.34277" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const ICON_HEART = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path d="M22 8.86222C22 10.4087 21.4062 11.8941 20.3458 12.9929C17.9049 15.523 15.5374 18.1613 13.0053 20.5997C12.4249 21.1505 11.5042 21.1304 10.9488 20.5547L3.65376 12.9929C1.44875 10.7072 1.44875 7.01723 3.65376 4.73157C5.88044 2.42345 9.50794 2.42345 11.7346 4.73157L11.9998 5.00642L12.2648 4.73173C13.3324 3.6245 14.7864 3 16.3053 3C17.8242 3 19.2781 3.62444 20.3458 4.73157C21.4063 5.83045 22 7.31577 22 8.86222Z" stroke-linejoin="round"/></svg>';
const ICON_FLAG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path d="M8 21L8 16M8 16V3.57709C8 3.10699 8.5161 2.81949 8.91581 3.06693L17.7061 8.50854C18.0775 8.73848 18.0866 9.2756 17.7231 9.51793L8 16Z" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const ICON_COMMUNITY = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path d="M7 18V17C7 14.2386 9.23858 12 12 12V12C14.7614 12 17 14.2386 17 17V18" stroke-linecap="round" stroke-linejoin="round"/><path d="M1 18V17C1 15.3431 2.34315 14 4 14V14" stroke-linecap="round" stroke-linejoin="round"/><path d="M23 18V17C23 15.3431 21.6569 14 20 14V14" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 12C13.6569 12 15 10.6569 15 9C15 7.34315 13.6569 6 12 6C10.3431 6 9 7.34315 9 9C9 10.6569 10.3431 12 12 12Z" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 14C5.10457 14 6 13.1046 6 12C6 10.8954 5.10457 10 4 10C2.89543 10 2 10.8954 2 12C2 13.1046 2.89543 14 4 14Z" stroke-linecap="round" stroke-linejoin="round"/><path d="M20 14C21.1046 14 22 13.1046 22 12C22 10.8954 21.1046 10 20 10C18.8954 10 18 10.8954 18 12C18 13.1046 18.8954 14 20 14Z" stroke-linecap="round" stroke-linejoin="round"/></svg>';

export { ICON_HEART, ICON_FLAG, ICON_COMMUNITY };

export interface TechComponent {
  icon: string;
  label: string;
}

export function decomposeTechnique(key: string): TechComponent[] {
  const components: TechComponent[] = [];
  if (key.startsWith('run_')) components.push({ icon: ICON_RUN, label: 'Run' });
  if (key === 'left_right')
    components.push({ icon: ICON_MOUSE_BOTH, label: 'Left + Right Click' });
  else if (key.includes('left'))
    components.push({ icon: ICON_MOUSE_LEFT, label: 'Left Click' });
  else if (key.includes('right'))
    components.push({ icon: ICON_MOUSE_RIGHT, label: 'Right Click' });
  if (key.includes('jump')) components.push({ icon: ICON_JUMP, label: 'Jump' });
  return components;
}

export const COMMUNITY_ICON = ICON_COMMUNITY;

export function isCommunityNade(nade: Nade): boolean {
  return !nade.source_url.includes('csnades.gg');
}

const DATA_DIR = process.env.NADES_DATA_DIR || import.meta.env.NADES_DATA_DIR || 'public/data';

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
