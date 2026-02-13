import { createHash } from 'node:crypto';

export function hashNickname(nickname: string): string {
  return createHash('sha256').update(nickname.trim().toLowerCase()).digest('hex');
}

export function getAccountHash(request: Request): string | null {
  const cookie = request.headers.get('cookie') || '';
  const match = cookie.match(/nades_account=([a-f0-9]{64})/);
  return match ? match[1] : null;
}
