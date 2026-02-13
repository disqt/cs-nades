import Database from 'better-sqlite3';
import { join } from 'node:path';

const DB_PATH = import.meta.env.NADES_DB_PATH || join(process.cwd(), 'cs-nades.db');

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH);
    _db.pragma('journal_mode = WAL');
    _db.pragma('foreign_keys = ON');
    initSchema(_db);
  }
  return _db;
}

export function initSchema(db: Database.Database): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS accounts (
      hash TEXT PRIMARY KEY,
      created_at INTEGER NOT NULL DEFAULT (unixepoch())
    );

    CREATE TABLE IF NOT EXISTS bookmarks (
      account_hash TEXT NOT NULL,
      slug TEXT NOT NULL,
      created_at INTEGER NOT NULL DEFAULT (unixepoch()),
      PRIMARY KEY (account_hash, slug),
      FOREIGN KEY (account_hash) REFERENCES accounts(hash)
    );

    CREATE TABLE IF NOT EXISTS reports (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      slug TEXT NOT NULL,
      frame_type TEXT NOT NULL CHECK (frame_type IN ('position', 'aim', 'result')),
      direction TEXT NOT NULL CHECK (direction IN ('earlier', 'later')),
      created_at INTEGER NOT NULL DEFAULT (unixepoch())
    );

    CREATE TABLE IF NOT EXISTS submissions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
      csnades_url TEXT,
      slug TEXT,
      map_name TEXT,
      data TEXT,
      submitted_at INTEGER NOT NULL DEFAULT (unixepoch()),
      reviewed_at INTEGER
    );
  `);
}
