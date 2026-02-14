import type { APIRoute } from 'astro';

export const GET: APIRoute = async () => {
  const base = import.meta.env.BASE_URL || '/cs/nades/';
  return new Response(null, {
    status: 302,
    headers: new Headers([
      ['Location', base],
      ['Set-Cookie', 'nades_account=; Path=/cs/nades/; HttpOnly; SameSite=Lax; Max-Age=0'],
      ['Set-Cookie', 'nades_account=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0'],
    ]),
  });
};
