// Renders index.html frame by frame in headless Chromium and pipes frames to ffmpeg.
// Usage: node render.js <outDir> [workers=4] [fps=30]   |   node render.js --stills <outDir> t1 t2 ...
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.json': 'application/json' };
function serve() {
  return new Promise(res => {
    const s = http.createServer((req, rsp) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { rsp.writeHead(404); return rsp.end(); }
      rsp.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(rsp);
    }).listen(0, () => res(s));
  });
}
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('pageerror', e.message));
  await page.goto(`http://localhost:${port}/index.html`);
  await page.waitForFunction('window.READY === true', null, { timeout: 120000 });
  return page;
}

(async () => {
  const server = await serve(); const port = server.address().port;
  const browser = await chromium.launch({ args: ARGS });
  if (process.argv[2] === '--stills') {
    const out = process.argv[3]; fs.mkdirSync(out, { recursive: true });
    const page = await openPage(browser, port);
    for (const ts of process.argv.slice(4)) {
      const t = Number(ts); const t0 = Date.now();
      await page.evaluate(t => window.seek(t), t);
      await page.screenshot({ path: path.join(out, `still_${ts.padStart(5, '0')}.jpg`), type: 'jpeg', quality: 90 });
      console.log('still', ts, Date.now() - t0, 'ms');
    }
  } else {
    const out = process.argv[2]; const workers = Number(process.argv[3] || 4); const fps = Number(process.argv[4] || 30);
    fs.mkdirSync(out, { recursive: true });
    const page0 = await openPage(browser, port);
    const total = Math.round(await page0.evaluate('window.DURATION') * fps); await page0.close();
    const per = Math.ceil(total / workers);
    const t0 = Date.now();
    await Promise.all([...Array(workers).keys()].map(async w => {
      const a = w * per, b = Math.min(total, a + per);
      const page = await openPage(browser, port);
      const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', String(fps), path.join(out, `seg_${w}.mp4`)], { stdio: ['pipe', 'inherit', 'inherit'] });
      for (let f = a; f < b; f++) {
        await page.evaluate(([t, f]) => window.seek(t, f), [f / fps, f]);
        const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
        if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
        if ((f - a) % 60 === 0) console.log(`worker ${w}: frame ${f}/${b} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
      }
      ff.stdin.end(); await new Promise(r => ff.on('close', r)); await page.close();
    }));
    fs.writeFileSync(path.join(out, 'segments.txt'), [...Array(workers).keys()].map(w => `file 'seg_${w}.mp4'`).join('\n'));
    console.log('done in', ((Date.now() - t0) / 1000).toFixed(0), 's');
  }
  await browser.close(); server.close();
})();
