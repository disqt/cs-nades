import type { APIRoute } from 'astro';
import { getDb } from '../../lib/db';

export const POST: APIRoute = async ({ request }) => {
  const { slug, frameType, direction } = await request.json();

  if (!slug || !['position', 'aim', 'result'].includes(frameType) ||
      !['earlier', 'later'].includes(direction)) {
    return new Response(JSON.stringify({ error: 'Invalid report data' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const db = getDb();
  db.prepare('INSERT INTO reports (slug, frame_type, direction) VALUES (?, ?, ?)').run(slug, frameType, direction);

  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
};
