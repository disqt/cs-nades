import type { APIRoute } from 'astro';
import { getDb } from '../../lib/db';
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB per file
const VALID_MAPS = new Set(['mirage', 'dust2', 'inferno', 'overpass', 'ancient', 'anubis', 'nuke']);
const VALID_THROW_TYPES = new Set(['left', 'right', 'left_jump', 'run_left']);

export const POST: APIRoute = async ({ request }) => {
  const formData = await request.formData();
  const csnadesUrl = formData.get('csnades_url') as string | null;
  const mapName = formData.get('map') as string | null;
  const side = formData.get('side') as string | null;

  const hasScreenshots = formData.has('position') && formData.has('aim') && formData.has('result');

  if (!csnadesUrl && !hasScreenshots) {
    return new Response(JSON.stringify({ error: 'Provide a csnades.gg URL or 3 screenshots' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  if (csnadesUrl) {
    try {
      const parsed = new URL(csnadesUrl);
      if (parsed.hostname !== 'csnades.gg' && parsed.hostname !== 'www.csnades.gg') {
        return new Response(JSON.stringify({ error: 'URL must be from csnades.gg' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    } catch {
      return new Response(JSON.stringify({ error: 'Invalid URL format' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  }

  if (hasScreenshots && !mapName) {
    return new Response(JSON.stringify({ error: 'Map name is required with screenshots' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  if (mapName && !VALID_MAPS.has(mapName)) {
    return new Response(JSON.stringify({ error: 'Invalid map name' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  if (side && !['t', 'ct'].includes(side)) {
    return new Response(JSON.stringify({ error: 'Invalid side value' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Extract new screenshot-mode fields
  const lineupName = formData.get('lineup_name') as string | null;
  const standDesc = formData.get('stand_desc') as string | null;
  const aimDesc = formData.get('aim_desc') as string | null;
  const throwType = formData.get('throw_type') as string | null;

  if (hasScreenshots) {
    if (!lineupName || !lineupName.trim()) {
      return new Response(JSON.stringify({ error: 'Lineup name is required with screenshots' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    if (!standDesc || !standDesc.trim()) {
      return new Response(JSON.stringify({ error: 'Stand description is required with screenshots' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    if (!aimDesc || !aimDesc.trim()) {
      return new Response(JSON.stringify({ error: 'Aim description is required with screenshots' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    if (!throwType || !VALID_THROW_TYPES.has(throwType)) {
      return new Response(JSON.stringify({ error: 'Valid throw type is required with screenshots' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  }

  // Validate file sizes before processing
  if (hasScreenshots) {
    for (const name of ['position', 'aim', 'result']) {
      const file = formData.get(name) as File;
      if (!file || file.size === 0) {
        return new Response(JSON.stringify({ error: `Missing ${name} screenshot` }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      if (file.size > MAX_FILE_SIZE) {
        return new Response(JSON.stringify({ error: `${name} screenshot exceeds 10 MB limit` }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }
  }

  const db = getDb();
  const result = db.prepare(
    'INSERT INTO submissions (csnades_url, map_name, side, data) VALUES (?, ?, ?, ?)'
  ).run(csnadesUrl, mapName, side, JSON.stringify({
    hasScreenshots: !!hasScreenshots,
    ...(hasScreenshots && {
      lineup_name: lineupName!.trim(),
      stand_desc: standDesc!.trim(),
      aim_desc: aimDesc!.trim(),
      throw_type: throwType,
    }),
  }));

  // Save screenshots to staging directory if uploaded
  if (hasScreenshots) {
    const stagingDir = join(process.cwd(), 'staging', String(result.lastInsertRowid));
    await mkdir(stagingDir, { recursive: true });

    for (const name of ['position', 'aim', 'result']) {
      const file = formData.get(name) as File;
      if (file && file.size > 0) {
        const buffer = Buffer.from(await file.arrayBuffer());
        // Use fixed filenames to prevent path traversal
        await writeFile(join(stagingDir, `${name}.jpg`), buffer);
      }
    }
  }

  return new Response(JSON.stringify({ ok: true, id: result.lastInsertRowid }), {
    headers: { 'Content-Type': 'application/json' },
  });
};
