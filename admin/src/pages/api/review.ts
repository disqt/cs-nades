import type { APIRoute } from 'astro';
import { getDb } from '../../lib/db';

export const POST: APIRoute = async ({ request }) => {
  const { id, status } = await request.json();

  if (!id || !['approved', 'rejected'].includes(status)) {
    return new Response(JSON.stringify({ error: 'Invalid data' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const db = getDb();
  db.prepare('UPDATE submissions SET status = ?, reviewed_at = unixepoch() WHERE id = ?').run(status, id);

  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
};
