// Renders the studio background in several variants.
// Usage: node design/render-studio.js   (needs playwright)
const { chromium } = require("playwright");
const path = require("path");
const variants = [
  ["studio.png", "w=1080&h=1920"],
  ["studio_ohne_schild.png", "w=1080&h=1920&sign=0"],
  ["studio_cyan.png", "w=1080&h=1920&hue=cyan"],
  ["studio_quer.png", "w=1920&h=1080"],
];
(async () => {
  const b = await chromium.launch();
  for (const [name, qs] of variants) {
    const [w, h] = qs.match(/w=(\d+)&h=(\d+)/).slice(1).map(Number);
    const p = await b.newPage({ viewport: { width: w, height: h } });
    await p.goto("file://" + path.join(__dirname, "studio-hintergrund.html") + "?" + qs);
    await p.waitForFunction(() => document.title === "ready");
    await p.evaluate(() => document.fonts.ready);
    const out = path.join(__dirname, "hintergruende", name);
    await p.screenshot({ path: out });
    console.log("saved", out);
    await p.close();
  }
  await b.close();
})();
