// Real touch hit-testing after asynchronous startup and first-run route picker.
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const s=window.__ski;
const result={passed:true,actions:[],warnings:[],touchChecks:[]};
const until=async(pred,label,timeout=45000)=>{
  const end=performance.now()+timeout;
  while(performance.now()<end){if(pred())return;await wait(200);}
  throw Error('Timed out: '+label);
};
if(!s)throw Error('Legacy engine QA API missing');
await s.ui().go();
await until(()=>s.ui().state==='run' && s.map.seen,'run state and first route picker');
s.map.open(false);
s.app().paused=false;
await until(()=>!s.avz.pickOpen && document.getElementById('app').classList.contains('run'),'route picker closed');
await wait(1500);
await snap('02-running');
for(const id of ['tuck','jump']){
  const button=document.getElementById(id);
  const r=button.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2;
  const hit=document.elementFromPoint(x,y);
  const details={id,x,y,width:r.width,height:r.height,hit:hit?.id||hit?.className||null,appClass:document.getElementById('app').className,pickerOpen:!!s.avz.pickOpen,uiState:s.ui().state,paused:s.app().paused,events:[]};
  const listener=e=>details.events.push({type:e.type,pointerType:e.pointerType,input:!!s.input().btn[id]});
  button.addEventListener('pointerdown',listener);
  button.addEventListener('pointerup',listener);
  if(!button.contains(hit)||r.width<44||r.height<44){
    result.passed=false;result.warnings.push(id+' is obscured or too small');
  } else {
    await tap(x,y,700);
    if(!details.events.some(e=>e.type==='pointerdown'&&e.pointerType==='touch')||!details.events.some(e=>e.type==='pointerup')){
      result.passed=false;result.warnings.push(id+' touch events missing');
    }
  }
  button.removeEventListener('pointerdown',listener);button.removeEventListener('pointerup',listener);
  result.touchChecks.push(details);result.actions.push(id);
}
await snap('03-after-touch');
await key('Escape',undefined,'Escape');await wait(1000);await snap('04-paused');
await key('Escape',undefined,'Escape');await wait(1000);
result.ready=!!s.app().ready;
result.passed=result.passed&&result.ready;
// Append this body before the upstream smoke probe's final "return result;".
// Frame cadence is a diagnostic of this headless runner, not a real device FPS.
const frameTimes=[];
const started=performance.now();
await new Promise(resolve=>{
  let previous=null;
  function measure(now){
    if(previous!==null)frameTimes.push(now-previous);
    previous=now;
    if(now-started>=3000) resolve(); else requestAnimationFrame(measure);
  }
  requestAnimationFrame(measure);
});
const sorted=frameTimes.slice().sort((a,b)=>a-b);
const percentile=p=>sorted.length?sorted[Math.min(sorted.length-1,Math.floor((sorted.length-1)*p))]:null;
const avg=frameTimes.length?frameTimes.reduce((a,b)=>a+b,0)/frameTimes.length:null;
result.performance={
  elapsedMs:performance.now()-started,
  frameIntervals:frameTimes.length,
  medianFrameMs:percentile(.5),
  p95FrameMs:percentile(.95),
  approximateRafHz:avg?1000/avg:null,
  viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio,touch:navigator.maxTouchPoints},
  canvas:[...document.querySelectorAll('canvas')].map(c=>({width:c.width,height:c.height})),
  heapBytes:performance.memory?.usedJSHeapSize??null,
  note:'Software-GPU headless Chrome diagnostic; not physical phone FPS or GPU memory.'
};
if(!frameTimes.length){result.passed=false;result.warnings.push('No frame cadence samples');}

return result;
