// Real mobile tap and native ride state. Test positioning only uses Game.relocate.
const s=window.__ski,result={passed:true,checks:[],warnings:[]};
const wait=ms=>new Promise(r=>setTimeout(r,ms));
function check(label,pass,details={}){result.checks.push({label,passed:!!pass,...details});if(!pass)throw Error(label);}
async function until(pred,label,timeout=45000){const t=performance.now()+timeout;while(performance.now()<t){if(pred())return;await wait(150);}throw Error('Timed out: '+label);}
const btn=()=>document.getElementById('fr-lift-action');
const visible=()=>{const b=btn();return b&&!b.hidden&&!b.disabled&&b.getBoundingClientRect().width>0;};
async function press(action,label){
  await until(()=>visible()&&btn().dataset.action===action,label);
  const b=btn(),r=b.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2;
  check(label+' hit test',r.width>=44&&r.height>=44&&x>=0&&x<innerWidth&&y>=0&&y<innerHeight&&b.contains(document.elementFromPoint(x,y)),{rect:[r.x,r.y,r.width,r.height],action,lift:b.dataset.lift});
  await tap(x,y,100);
}
try{
  check('Touch environment',navigator.maxTouchPoints>0||matchMedia('(pointer:coarse)').matches);
  await s.ui().go();
  await until(()=>s.ui().state==='run'&&s.map.seen,'route picker');
  const free=s.map.items.find(it=>it.kind==='free');
  check('Free route available',!!free);
  s.map.go('free',free.i);s.map.open(false);s.app().paused=false;
  await until(()=>!s.avz.pickOpen&&s.game().mode==='run'&&s.map.state().mode==='free'&&btn(),'free mode');
  s.tod('day');
  await until(()=>s.avz.lift&&!s.avz.lift.closed()&&s.town.car?.lifts?.length,'daytime lifts');
  const rendered=new Set(s.town.car.lifts.map(l=>l.name));
  const all=s.map.lifts.filter(l=>l.a1-l.a0>20);
  let picked=null;
  for(const l of all){
    if(!rendered.has(l.n))continue;
    const b=l.p[0];
    for(const r of [6,12,20])for(let i=0;i<12;i++){
      const x=b[0]+r*Math.cos(i*Math.PI/6),z=b[1]+r*Math.sin(i*Math.PI/6);
      if(s.avz.wall(x,z,1.8))continue;
      if(all.some(q=>q!==l&&Math.hypot(q.p[0][0]-x,q.p[0][1]-z)<r+2))continue;
      picked={l,x,z};break;
    }
    if(picked)break;
  }
  check('Real rendered lift and lower-station fixture',!!picked);
  const {l,x,z}=picked;
  const far=AVZ_DATA.pistes.flatMap(p=>p.p).find(p=>all.every(q=>Math.hypot(q.p[0][0]-p[0],q.p[0][1]-p[1])>120)&&!s.avz.wall(p[0],p[1],1.8));
  check('Away-from-lift fixture',!!far);
  s.game().relocate(far[0],far[1]);
  await until(()=>!visible(),'button hidden away');
  check('Hidden away from station',!visible());
  s.game().relocate(x,z);
  await until(()=>visible()&&btn().dataset.action==='board','near station');
  check('Correct nearby lift',btn().dataset.lift===l.n,{lift:l.n});
  s.map.open(true,'routes');await until(()=>!visible(),'menu hides lift action');
  check('Hidden in menu',!visible());
  s.map.open(false);s.app().paused=false;
  await until(()=>visible(),'restored action');
  await snap('02-lift-station');
  await press('board','Board touch target');
  await until(()=>s.map.test.riding()&&visible()&&btn().dataset.action==='summit','native ride started');
  const pos=s.avz.lift.pos();
  check('Actual lift riding',s.map.test.riding()&&!!pos&&pos.every(Number.isFinite)&&s.avz.hold===true,{lift:l.n,pos});
  await snap('03-lift-riding');
  await press('summit','Summit touch target');
  await until(()=>!s.map.test.riding()&&!s.avz.hold,'native lift finished');
  const top=l.p[l.p.length-1],p=s.game().s.p;
  check('Arrived near actual upper station',Math.hypot(p[0]-top[0],p[2]-top[1])<=320,{lift:l.n,position:p.slice(),top});
  check('Simulation running',s.game().mode==='run'&&s.app().ready&&!s.map.test.riding());
  await snap('04-lift-summit');
}catch(e){result.passed=false;result.warnings.push(String(e.stack||e));}
return result;
