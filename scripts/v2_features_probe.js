// v2 targeted input and camera regression. Executed by the pinned QA harness.
const s=window.__ski;
const result={passed:true,actions:[],warnings:[],checks:[]};
const wait=ms=>new Promise(r=>setTimeout(r,ms));
function check(label,pass,details={}){
  result.checks.push({label,passed:!!pass,...details});
  if(!pass){result.passed=false;result.warnings.push(label);}
}
async function until(pred,label,timeout=45000){
  const end=performance.now()+timeout;
  while(performance.now()<end){if(pred())return;await wait(200);}
  throw Error('Timed out: '+label);
}
async function clickVisible(selector,label){
  const el=document.querySelector(selector);
  if(!el)throw Error('Missing '+selector);
  const r=el.getBoundingClientRect();
  const hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
  check(label+' hit test',r.width>0&&r.height>0&&el.contains(hit));
  if(!el.contains(hit))throw Error('Obscured '+selector);
  if(navigator.maxTouchPoints>0)await tap(r.left+r.width/2,r.top+r.height/2,80);
  else el.click(); // actual UI handler; keyboard used for the desktop switch.
}
try{
  if(!s||FR_RESORT.engineVersion!==2)throw Error('v2 engine missing');
  await s.ui().go();
  await until(()=>s.ui().state==='run'&&s.map.seen,'first route picker');
  s.map.open(true,'gear');
  await until(()=>document.querySelector('[data-ride="1"]')?.getBoundingClientRect().height>0,'equipment menu');
  await clickVisible('[data-ride="1"]','Snowboard equipment');
  check('Snowboard selected',s.avz.board===true);
  await clickVisible('[data-stance="0"]','Regular stance');
  check('Regular stance selected',s.avz.stance==='regular'&&s.avz.sbSg===1);
  s.map.open(false);s.app().paused=false;
  await until(()=>!s.avz.pickOpen&&s.game().mode==='run','resume game');
  await until(()=>document.getElementById('sb-sw')?.getBoundingClientRect().height>0,'switch button');
  await snap('02-snowboard-regular');
  const before=s.avz.stance;
  if(navigator.maxTouchPoints>0)await clickVisible('#sb-sw','Touch switch');
  else await key('KeyZ',undefined,'z');
  await until(()=>s.avz.stance!==before,'animated stance switch');
  check('Switch regular to goofy',s.avz.stance==='goofy'&&s.avz.sbSg===-1);
  await wait(1000);
  await snap('03-snowboard-goofy');
  if(navigator.maxTouchPoints>0)await clickVisible('#sb-sw','Touch switch back');
  else await key('KeyZ',undefined,'z');
  await until(()=>s.avz.stance==='regular','animated stance switch back');
  check('Switch goofy to regular',s.avz.sbSg===1);
  const oldView=s.game().view;
  await key('KeyV',undefined,'v');
  await until(()=>s.game().view!==oldView,'camera hotkey');
  check('Camera changed',s.game().views.some(v=>v.id===s.game().view),{from:oldView,to:s.game().view});
  // A camera enum change is insufficient: require an actual first-person draw.
  const fp=s.game().fpv;
  await until(()=>fp.dead||fp.frDraw?.mode==='regular','regular first-person draw');
  check('First-person regular mesh renders without fallback',!fp.dead&&fp.frDraw?.count>0,{draw:fp.frDraw});
  await snap('04-camera');
  if(navigator.maxTouchPoints>0)await clickVisible('#sb-sw','FPV touch switch');
  else await key('KeyZ',undefined,'z');
  await until(()=>fp.dead||(s.avz.stance==='goofy'&&fp.frDraw?.mode==='goofy'),'goofy first-person draw');
  check('First-person goofy mesh renders without fallback',!fp.dead&&fp.frDraw?.mode==='goofy'&&fp.frDraw?.count>0,{draw:fp.frDraw});
  await snap('04b-camera-goofy');
  s.game().setView('chase',true);
  const initial=s.game().s.p.slice();
  await key('ArrowLeft',true,'ArrowLeft');await wait(600);await key('ArrowLeft',false,'ArrowLeft');
  await key('ArrowRight',true,'ArrowRight');await wait(600);await key('ArrowRight',false,'ArrowRight');
  const state=s.game().s;
  check('Finite simulation state',[...state.p,...state.v,state.speed].every(Number.isFinite),{start:initial,end:state.p.slice(),speed:state.speed});
  // Ground clearance of the new camera collision helper, not a full wall collision test.
  const p=state.p.slice(),camera=[p[0]+2,p[1]-10,p[2]+2];
  s.avz.clipCam(camera,p);
  check('Camera terrain clearance',camera.every(Number.isFinite)&&camera[1]>=s.m.Course.height(camera[0],camera[2],0.5)+0.379,{camera});
  s.map.open(true,'gear');
  await until(()=>document.querySelector('[data-ride="0"]')?.getBoundingClientRect().height>0,'return equipment menu');
  await clickVisible('[data-ride="0"]','Ski equipment');
  check('Return to skis',s.avz.board===false);
  s.map.open(false);s.app().paused=false;
  s.game().setView('fp',true);
  await until(()=>fp.dead||fp.frDraw?.mode==='ski','ski first-person draw');
  check('First-person ski mesh renders without fallback',!fp.dead&&fp.frDraw?.mode==='ski'&&fp.frDraw?.count>0,{draw:fp.frDraw});
  check('Ready after mode changes',s.app().ready===true&&!fp.dead);
  await snap('05-return-to-skis');
}catch(e){result.passed=false;result.warnings.push(String(e.stack||e));}
return result;
