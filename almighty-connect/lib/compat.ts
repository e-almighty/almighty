// Runtime compatibility for older iPads (iPadOS 13-15.3). Import first in client entry modules.
// Without these, a receiver iPad on iPadOS 15.3 or earlier rendered a blank page because
// crypto.randomUUID does not exist there and the heartbeat effect threw before paint.
// app/layout.tsx carries the same polyfills as an inline script so the router loads too.
declare global { interface Window { __almightyCompatLoaded?: boolean } }

type Settled = { status: 'fulfilled'; value: unknown } | { status: 'rejected'; reason: unknown };
type Globals = {
  Object: { hasOwn?: (o: object, k: PropertyKey) => boolean };
  Array: { prototype: { at?: (n: number) => unknown } };
  String: { prototype: { replaceAll?: (s: string | RegExp, r: string | ((m: string) => string)) => string } };
  Promise: { allSettled?: (l: Iterable<unknown>) => Promise<Settled[]> };
};

export function newId(): string {
  const c = typeof crypto !== 'undefined' ? crypto : undefined;
  if (c && typeof c.randomUUID === 'function') {
    try { return c.randomUUID(); } catch { /* fall through to the manual generator */ }
  }
  const bytes = new Uint8Array(16);
  if (c && typeof c.getRandomValues === 'function') c.getRandomValues(bytes);
  else for (let i = 0; i < 16; i++) bytes[i] = Math.floor(Math.random() * 256);
  bytes[6] = (bytes[6] & 0x0f) | 0x40; // version 4
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // variant 10
  const hex = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function installCompat() {
  if (typeof window === 'undefined' || window.__almightyCompatLoaded) return;
  window.__almightyCompatLoaded = true;
  const g = globalThis as unknown as Globals;
  try {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID !== 'function') {
      Object.defineProperty(crypto, 'randomUUID', { value: () => newId(), configurable: true, writable: true });
    }
  } catch { /* read-only crypto object; newId() is used directly by this app */ }
  if (typeof g.Object.hasOwn !== 'function') {
    g.Object.hasOwn = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  }
  if (typeof g.Array.prototype.at !== 'function') {
    Object.defineProperty(Array.prototype, 'at', { value: function (this: unknown[], n: number) { n = Math.trunc(n) || 0; if (n < 0) n += this.length; return n < 0 || n >= this.length ? undefined : this[n]; }, configurable: true, writable: true });
  }
  if (typeof g.String.prototype.replaceAll !== 'function') {
    Object.defineProperty(String.prototype, 'replaceAll', { value: function (this: string, s: string | RegExp, r: string | ((m: string) => string)) { return typeof s === 'string' ? this.split(s).join(typeof r === 'function' ? r(s) : r) : this.replace(s, r as string); }, configurable: true, writable: true });
  }
  if (typeof g.Promise.allSettled !== 'function') {
    g.Promise.allSettled = (list) => Promise.all(Array.from(list, p => Promise.resolve(p).then<Settled, Settled>(value => ({ status: 'fulfilled', value }), reason => ({ status: 'rejected', reason }))));
  }
}

installCompat();
