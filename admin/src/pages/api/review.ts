import type { APIRoute } from 'astro';
import { getDb } from '../../lib/db';
import { rm } from 'node:fs/promises';
import { join } from 'node:path';

export const POST: APIRoute = async ({ request }) => {
  const { id, status } = await request.json();

  if (!id || !['approved', 'rejected', 'deleted'].includes(status)) {
    return new Response(JSON.stringify({ error: 'Invalid data' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const db = getDb();

  if (status === 'deleted') {
    // Remove staging files if they exist
    const stagingDir = join(process.cwd(), '..', 'staging', String(id));
    await rm(stagingDir, { recursive: true, force: true });
    // Remove from DB
    db.prepare('DELETE FROM submissions WHERE id = ?').run(id);
  } else {
    db.prepare('UPDATE submissions SET status = ?, reviewed_at = unixepoch() WHERE id = ?').run(status, id);
  }

  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
};
