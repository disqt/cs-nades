import type { APIRoute } from 'astro';
import { getAccountHash } from '../../lib/auth';
import { getDb } from '../../lib/db';

export const POST: APIRoute = async ({ request }) => {
  const hash = getAccountHash(request);
  if (!hash) {
    return new Response(JSON.stringify({ error: 'Not logged in' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const { slug } = await request.json();
  if (!slug) {
    return new Response(JSON.stringify({ error: 'Missing slug' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const db = getDb();
  const existing = db.prepare('SELECT 1 FROM bookmarks WHERE account_hash = ? AND slug = ?').get(hash, slug);

  if (existing) {
    db.prepare('DELETE FROM bookmarks WHERE account_hash = ? AND slug = ?').run(hash, slug);
    return new Response(JSON.stringify({ bookmarked: false }), {
      headers: { 'Content-Type': 'application/json' },
    });
  } else {
    db.prepare('INSERT INTO bookmarks (account_hash, slug) VALUES (?, ?)').run(hash, slug);
    return new Response(JSON.stringify({ bookmarked: true }), {
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
