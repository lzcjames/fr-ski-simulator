// Run actual HTTP browser navigation in a single persistent Chromium profile.
// Never use request interception, which disables Chromium HTTP cache.
import { chromium } from 'playwright-core';
import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import os from 'node:os';
import assert from 'node:assert/strict';

const root=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
await fs.mkdir(out,{recursive:true});
const manifest=JSON.parse(await fs.readFile(path.join(root,'online-catalog.json'),'utf8'));
const requests=[];
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.png':'image/png'};
const allowed=new Set(manifest.assets.map(a=>'/'+a.path));
const server=http.createServer(async(req,res)=>{
  try{
    const url=new URL(req.url,'http://127.0.0.1');
    const file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
    if(!file.startsWith(root+path.sep))throw Error('invalid path');
    const data=await fs.readFile(file);
    const cached=allowed.has(url.pathname);
    requests.push({path:url.pathname,bytes:data.length});
    res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream',
      'Cache-Control':cached?'public, max-age=31536000, immutable':'no-store',
      'X-Content-Type-Options':'nosniff'});
    res.end(data);
  }catch{res.writeHead(404);res.end();}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin='http://127.0.0.1:'+server.address().port;
const profile=await fs.mkdtemp(path.join(os.tmpdir(),'frski-cache-'));
const report={passed:false,resorts:[],requests,externalRequests:[],errors:[]};
let context;
try{
  context=await chromium.launchPersistentContext(profile,{
    executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',
    headless:true,viewport:{width:960,height:540},
    args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',
          '--ignore-gpu-blocklist','--disk-cache-size=134217728',
          '--disable-background-networking','--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1']
  });
  const page=context.pages()[0]||await context.newPage();
  page.on('pageerror',err=>report.errors.push(String(err)));
  page.on('console',msg=>{if(msg.type()==='error')report.errors.push(msg.text())});
  page.on('request',req=>{if(!req.url().startsWith(origin+'/')&&!/^(data:|blob:|about:)/.test(req.url()))report.externalRequests.push(req.url())});
  const seen=new Set();
  for(const row of manifest.resorts){
    const from=requests.length,t0=Date.now();
    await page.goto(origin+'/'+row.play+'?backend=webgl2&lang=en',{waitUntil:'load',timeout:180000});
    await page.waitForFunction(()=>window.__ski?.app()?.ready,{timeout:180000},{timeout:180000});
    const game=await page.evaluate(()=>({name:FR_RESORT.name,slug:FR_RESORT.slug,backend:window.__ski.app().gfx.caps.backend,grids:AVZ_DATA.grids.map(g=>g.step),routes:AVZ_DATA.courses.length}));
    assert.equal(game.slug,row.slug);assert.equal(game.backend,'webgl2');
    assert.deepEqual(game.grids,[5,20,60]);assert.ok(game.routes>0);
    const readyMs=Date.now()-t0;
    await page.evaluate(async()=>{await window.__ski.ui().go()});
    await page.waitForFunction(()=>window.__ski.ui().state==='run'&&window.__ski.map.seen,null,{timeout:60000});
    await page.evaluate(()=>{window.__ski.map.open(false);window.__ski.app().paused=false});
    await page.waitForFunction(()=>!window.__ski.avz.pickOpen&&document.getElementById('app').classList.contains('run'),null,{timeout:60000});
    await page.keyboard.down('ArrowLeft');await page.waitForTimeout(500);await page.keyboard.up('ArrowLeft');
    await page.keyboard.down('Shift');await page.waitForTimeout(500);await page.keyboard.up('Shift');
    await page.screenshot({path:path.join(out,row.slug+'.png'),timeout:60000});
    const fetched=requests.slice(from).filter(r=>allowed.has(r.path));
    for(const asset of row.assets){
      const rel='/'+asset;
      if(seen.has(asset)) assert.equal(fetched.filter(r=>r.path===rel).length,0,'cached asset requested again: '+asset);
      else assert.equal(fetched.filter(r=>r.path===rel).length,1,'missing or duplicate initial asset: '+asset);
      seen.add(asset);
    }
    const resourceTiming=await page.evaluate(()=>performance.getEntriesByType('resource').filter(r=>r.name.includes('/assets/')).map(r=>({name:r.name,transferSize:r.transferSize,encodedBodySize:r.encodedBodySize})));
    report.resorts.push({slug:row.slug,readyMs,game,sharedRequests:fetched,sharedTransferBytes:fetched.reduce((a,r)=>a+r.bytes,0),resourceTiming});
  }
  assert.equal(report.errors.length,0,JSON.stringify(report.errors));
  assert.equal(report.externalRequests.length,0,JSON.stringify(report.externalRequests));
  report.passed=true;
}catch(e){report.error=String(e.stack||e);process.exitCode=1;}
finally{
  await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
  await context?.close();await new Promise(r=>server.close(r));
  await fs.rm(profile,{recursive:true,force:true});
}
