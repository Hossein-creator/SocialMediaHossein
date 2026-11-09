// Renders a graphics layer as transparent PNG frames.
// Usage: node editor/render-overlay.js <projekt-ordner> <frames-ordner> <under|over> [nur-sekunde]
//   under = B-roll/slides (behind you), over = subtitles, titles, stickers (in front of you)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const proj = path.resolve(process.argv[2]);
  const out = path.resolve(process.argv[3]);
  const layer = process.argv[4] || 'over';
  const only = process.argv[5] !== undefined ? parseFloat(process.argv[5]) : null;
  const tl = JSON.parse(fs.readFileSync(path.join(proj, 'timeline.json'), 'utf8'));
  const wf = path.join(proj, 'words.json');
  if (!tl.words && fs.existsSync(wf)) tl.words = JSON.parse(fs.readFileSync(wf, 'utf8'));
  fs.mkdirSync(out, { recursive: true });
  const url = 'file://' + path.resolve(__dirname, 'overlay.html');
  const fps = tl.fps || 30;
  const total = Math.round(tl.duration * fps);
  let frames = only !== null ? [Math.round(only * fps)] : [...Array(total).keys()];
  if (layer === 'under' && only === null) {
    // only frames where a B-roll scene is visible; the compositor treats missing frames as empty
    const sc = (tl.scenes || []).filter((s) => s.broll);
    frames = frames.filter((f) => sc.some((s) => f / fps >= s.t0 && f / fps < s.t1));
  }
  const workers = only !== null ? 1 : 4;
  const browser = await chromium.launch();
  let done = 0;
  await Promise.all([...Array(workers).keys()].map(async (w) => {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
    await page.goto(url);
    await page.evaluate(([tl, layer]) => { window.build(tl); window.setLayer(layer); }, [tl, layer]);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    for (let i = w; i < frames.length; i += workers) {
      const f = frames[i];
      await page.evaluate((t) => window.setTime(t), f / fps);
      await page.screenshot({ path: path.join(out, `f${String(f).padStart(5, '0')}.png`), omitBackground: true });
      if (++done % 300 === 0) console.log(`${layer}: ${done}/${frames.length}`);
    }
  }));
  await browser.close();
  console.log(`${layer} frames done`, frames.length);
})();
