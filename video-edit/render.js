// Offline render of preview.html to an MP4: steps the page frame by frame at 1920x1080,
// renders the audio mix offline, then muxes with ffmpeg.
// usage: node render.js <url-to-preview.html> <out.mp4> [voice=male] [hook=A] [fps=30]
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');
const [url, out, voice = 'male', hook = 'A', fps = '30'] = process.argv.slice(2);
const FPS = +fps, W = 1920, H = 1080;

(async () => {
  const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const page = await browser.newPage({ viewport: { width: W + 200, height: H + 400 } });
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.goto(url);
  await page.addStyleTag({ content: `body{margin:0} .wrap{max-width:none;padding:0} #stageWrap{width:${W}px!important;max-width:none;border:0;border-radius:0}
    #tag,#bigplay,#loading{display:none!important}` });
  await page.waitForFunction(() => window.__lab, null, { timeout: 30000 });
  await page.waitForTimeout(6000); // footage + VO decode
  await page.selectOption('#hookSel', hook);
  await page.waitForTimeout(500);
  const dur = await page.evaluate(() => window.__lab.duration());

  console.log(`audio: rendering ${dur.toFixed(1)}s mix (voice=${voice}, hook=${hook})`);
  const wav = await page.evaluate(v => window.__lab.audio(v), voice);
  fs.writeFileSync(out + '.wav', Buffer.from(wav, 'base64'));

  const frames = Math.round(Math.min(dur, +process.env.LIMIT || dur) * FPS); // LIMIT=seconds for a quick test
  const enc = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', out + '.video.mp4'], { stdio: ['pipe', 'inherit', 'inherit'] });
  const box = await page.locator('#stageWrap').boundingBox();
  const clip = { x: Math.round(box.x), y: Math.round(box.y), width: W, height: H }; // exact 1920x1080
  const t0 = Date.now();
  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.__lab.frame(t), i / FPS);
    const png = await page.screenshot({ type: 'png', clip, animations: 'disabled' });
    if (!enc.stdin.write(png)) await new Promise(r => enc.stdin.once('drain', r));
    if (i % 60 === 0) console.log(`frame ${i}/${frames}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  enc.stdin.end(); await new Promise(r => enc.on('close', r));
  await browser.close();

  // mux; master the mix to -14 LUFS for social platforms
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', out + '.video.mp4', '-i', out + '.wav',
    '-af', 'loudnorm=I=-14:TP=-1:LRA=9', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
    '-movflags', '+faststart', '-shortest', out], { stdio: 'inherit' });
  fs.unlinkSync(out + '.video.mp4'); fs.unlinkSync(out + '.wav');
  console.log('done', out);
})();
