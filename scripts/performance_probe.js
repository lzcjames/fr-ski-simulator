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
