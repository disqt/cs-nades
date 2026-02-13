import { describe, it, expect, beforeEach } from 'vitest';
import Database from 'better-sqlite3';
import { initSchema } from '../db';

describe('initSchema', () => {
  let db: Database.Database;

  beforeEach(() => {
    db = new Database(':memory:');
    initSchema(db);
  });

  it('creates accounts table', () => {
    const info = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'").get();
    expect(info).toBeTruthy();
  });

  it('creates bookmarks table with foreign key', () => {
    db.prepare("INSERT INTO accounts (hash) VALUES ('abc')").run();
    db.prepare("INSERT INTO bookmarks (account_hash, slug) VALUES ('abc', 'test-slug')").run();
    const row = db.prepare("SELECT * FROM bookmarks WHERE account_hash = 'abc'").get() as any;
    expect(row.slug).toBe('test-slug');
  });

  it('creates reports table with constraints', () => {
    db.prepare("INSERT INTO reports (slug, frame_type, direction) VALUES ('test', 'aim', 'earlier')").run();
    const row = db.prepare("SELECT * FROM reports WHERE slug = 'test'").get() as any;
    expect(row.direction).toBe('earlier');
  });

  it('creates submissions table with default status', () => {
    db.prepare("INSERT INTO submissions (csnades_url, map_name) VALUES ('https://example.com', 'mirage')").run();
    const row = db.prepare("SELECT * FROM submissions WHERE map_name = 'mirage'").get() as any;
    expect(row.status).toBe('pending');
  });

  it('enforces bookmark uniqueness', () => {
    db.prepare("INSERT INTO accounts (hash) VALUES ('abc')").run();
    db.prepare("INSERT INTO bookmarks (account_hash, slug) VALUES ('abc', 'slug1')").run();
    expect(() =>
      db.prepare("INSERT INTO bookmarks (account_hash, slug) VALUES ('abc', 'slug1')").run()
    ).toThrow();
  });

  it('enforces valid frame_type', () => {
    expect(() =>
      db.prepare("INSERT INTO reports (slug, frame_type, direction) VALUES ('x', 'invalid', 'earlier')").run()
    ).toThrow();
  });

  it('enforces valid direction', () => {
    expect(() =>
      db.prepare("INSERT INTO reports (slug, frame_type, direction) VALUES ('x', 'aim', 'invalid')").run()
    ).toThrow();
  });

  it('enforces valid submission status', () => {
    expect(() =>
      db.prepare("INSERT INTO submissions (status, map_name) VALUES ('invalid', 'mirage')").run()
    ).toThrow();
  });
});
