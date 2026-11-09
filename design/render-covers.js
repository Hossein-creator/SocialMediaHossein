// Renders cover images (1080x1920) from cover-vorlage.html.
// Usage: node design/render-covers.js inhalte/woche-01/covers.json
// The JSON file holds a list of { file, series, title, sub, part }; images are saved next to it in covers/.
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const listFile = path.resolve(process.argv[2]);
  const items = JSON.parse(fs.readFileSync(listFile, 'utf8'));
  const outDir = path.join(path.dirname(listFile), 'covers');
  fs.mkdirSync(outDir, { recursive: true });
  const template = 'file://' + path.resolve(__dirname, 'cover-vorlage.html');

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  for (const it of items) {
    const qs = new URLSearchParams({ series: it.series || '', title: it.title, sub: it.sub || '', part: it.part || '' });
    await page.goto(template + '?' + qs.toString());
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(outDir, it.file) });
    console.log('saved', it.file);
  }
  await browser.close();
})();
