// Company-provided pilot link. Keep each store isolated when adding more links.
export const MEET_LINKS: Readonly<Record<string, string>> = {
 A: 'https://meet.google.com/hom-rzvi-dbm',
};
export function meetLink(store: string): string | null {
 return MEET_LINKS[store] ?? null;
}
