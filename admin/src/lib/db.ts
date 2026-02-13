import Database from 'better-sqlite3';
import { join } from 'node:path';

const DB_PATH = import.meta.env.NADES_DB_PATH || process.env.NADES_DB_PATH || join(process.cwd(), '..', 'cs-nades.db');

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH);
    _db.pragma('journal_mode = WAL');
    _db.pragma('foreign_keys = ON');
  }
  return _db;
}
