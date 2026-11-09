// Renders the animated graphics layer (transparent PNG frames) for a project.
// Usage: node editor/render-overlay.js <projekt-ordner> <frames-ordner> [nur-sekunde]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const proj = path.resolve(process.argv[2]);
  const out = path.resolve(process.argv[3]);
  const only = process.argv[4] !== undefined ? parseFloat(process.argv[4]) : null;
  const tl = JSON.parse(fs.readFileSync(path.join(proj, 'timeline.json'), 'utf8'));
  fs.mkdirSync(out, { recursive: true });
  const url = 'file://' + path.resolve(__dirname, 'overlay.html');
  const fps = tl.fps || 30;
  const total = Math.round(tl.duration * fps);
  const frames = only !== null ? [Math.round(only * fps)] : [...Array(total).keys()];
  const workers = only !== null ? 1 : 4;

  const browser = await chromium.launch();
  let done = 0;
  await Promise.all([...Array(workers).keys()].map(async (w) => {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
    await page.goto(url);
    await page.evaluate((tl) => window.build(tl), tl);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    for (let i = w; i < frames.length; i += workers) {
      const f = frames[i];
      await page.evaluate((t) => window.setTime(t), f / fps);
      await page.screenshot({ path: path.join(out, `f${String(f).padStart(5, '0')}.png`), omitBackground: true });
      if (++done % 150 === 0) console.log(`${done}/${frames.length}`);
    }
  }));
  await browser.close();
  console.log('frames done', frames.length);
})();
