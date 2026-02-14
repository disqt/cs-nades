import type { APIRoute } from 'astro';
import { getDb } from '../../lib/db';

const VALID_REASONS = ['outdated', 'doesnt_work', 'wrong_map', 'other'];

export const POST: APIRoute = async ({ request }) => {
  const { slug, reason } = await request.json();

  if (!slug || !VALID_REASONS.includes(reason)) {
    return new Response(JSON.stringify({ error: 'Invalid report data' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const db = getDb();
  db.prepare('INSERT INTO lineup_reports (slug, reason) VALUES (?, ?)').run(slug, reason);

  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
};
