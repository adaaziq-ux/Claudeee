// Render only the audio mix of preview.html to a WAV (e.g. to swap the voice on an existing render).
// usage: node render-audio.js <url-to-preview.html> <out.wav> [voice=male|female|off] [hook=A]
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');
const fs = require('fs');
const [url, out, voice = 'off', hook = 'A'] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(url);
  await page.waitForFunction(() => window.__lab, null, { timeout: 30000 });
  await page.waitForTimeout(4000);
  await page.selectOption('#hookSel', hook);
  const wav = await page.evaluate(v => window.__lab.audio(v), voice);
  fs.writeFileSync(out, Buffer.from(wav, 'base64'));
  await browser.close();
  console.log('wrote', out);
})();
