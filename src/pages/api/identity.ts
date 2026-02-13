import type { APIRoute } from 'astro';
import { hashNickname } from '../../lib/auth';
import { getDb } from '../../lib/db';

export const POST: APIRoute = async ({ request }) => {
  const body = await request.json();
  const nickname = body.nickname?.trim();

  if (!nickname || nickname.length < 3) {
    return new Response(JSON.stringify({ error: 'Nickname must be at least 3 characters' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const hash = hashNickname(nickname);
  const db = getDb();

  db.prepare('INSERT OR IGNORE INTO accounts (hash) VALUES (?)').run(hash);

  const bookmarks = db.prepare('SELECT slug FROM bookmarks WHERE account_hash = ?').all(hash) as { slug: string }[];

  return new Response(JSON.stringify({ ok: true, bookmarks: bookmarks.map(b => b.slug) }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Set-Cookie': `nades_account=${hash}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${60 * 60 * 24 * 365}`,
    },
  });
};

export const DELETE: APIRoute = async () => {
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Set-Cookie': 'nades_account=; Path=/; HttpOnly; Max-Age=0',
    },
  });
};
