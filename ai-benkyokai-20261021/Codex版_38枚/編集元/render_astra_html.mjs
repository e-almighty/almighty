import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'file:///C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';

const root = 'C:/Users/user/Documents/Codex/2026-10-19/ai-ai';
const file = path.join(root, 'outputs/2026-10-21_Astra勉強会_38枚.html');
const out = path.join(root, 'work/screenshots/final');
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  args: ['--no-sandbox', '--disable-gpu'],
});
const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
await page.goto('file:///' + file.replaceAll('\\', '/'));
await page.waitForTimeout(250);
const count = await page.locator('section.xop-slide').count();
const audit = [];
for (let i = 1; i <= count; i++) {
  await page.evaluate(n => window.template_show(n - 1), i);
  await page.waitForTimeout(35);
  const view = await page.evaluate(() => {
    const active = document.querySelector('section.xop-slide.is-active');
    const canvas = active?.querySelector('.xop-canvas');
    const rect = canvas?.getBoundingClientRect();
    const elems = Array.from(active?.querySelectorAll('.semantic-layer .sem-paper > *') ?? []);
    return {
      title: active?.getAttribute('aria-label') ?? '',
      canvas: rect && { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      overflow: elems.filter(e => {
        const r = e.getBoundingClientRect();
        return r.left < rect.left - 1 || r.right > rect.right + 1 || r.top < rect.top - 1 || r.bottom > rect.bottom + 1;
      }).map(e => e.className || e.tagName),
    };
  });
  audit.push({ slide: i, ...view });
  await page.screenshot({ path: path.join(out, 'slide_' + String(i).padStart(3,'0') + '.png') });
}
await page.evaluate(() => {
  document.querySelectorAll('section.xop-slide').forEach(s => s.classList.add('is-active'));
});
await page.pdf({ path: path.join(root, 'outputs/2026-10-21_Astra勉強会_38枚.pdf'), width: '16in', height: '9in', printBackground: true, preferCSSPageSize: true });
await fs.writeFile(path.join(root,'work/render_audit.json'), JSON.stringify(audit,null,2),'utf8');
await browser.close();
console.log(JSON.stringify({ count, overflowing: audit.filter(x => x.overflow.length), screenshots: out }));
