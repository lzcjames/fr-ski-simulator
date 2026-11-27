"""Add an actual touch lift action to the original AVZMap navigation HUD."""
def patch_mobile_lift(src):
    def rep(old,new):
        nonlocal src
        if src.count(old)!=1:raise ValueError("mobile lift anchor mismatch: "+old[:100])
        src=src.replace(old,new,1)
    rep("</style>", """
/* Touch lift action: keep the original ski controls and map layout. */
#app.avz-ui #hud .avz-mini #fr-lift-action {
  position:relative;display:block;width:100%;min-width:44px;min-height:44px;
  margin-top:8px;padding:8px 5px;box-sizing:border-box;
  border:1px solid rgba(244,247,252,.65);border-radius:8px;
  background:rgba(12,28,40,.92);color:#fff;font:600 12px/1.3 system-ui,sans-serif;
  white-space:normal;overflow-wrap:anywhere;pointer-events:auto;
  touch-action:manipulation;cursor:pointer;-webkit-tap-highlight-color:transparent;
}
#app.avz-ui #hud .avz-mini #fr-lift-action[hidden] {display:none!important}
#app.avz-ui #hud .avz-mini #fr-lift-action:active {background:#315c79}
</style>""")
    rep("  const coarse = () => { try { return matchMedia('(pointer:coarse)').matches; } catch (e) { return false; } };",
        """  const coarse = () => { try { return matchMedia('(pointer:coarse)').matches; } catch (e) { return false; } };
  let frLiftBtn = null;
  const frTouch = () => coarse() || navigator.maxTouchPoints > 0;
  // Re-evaluate the live position, not a stale nearLift from the last HUD tick.
  const frLiftChoice = () => {
    if (!frTouch() || Game.mode !== 'run' || !Game.s || open || photo || AVZ.fin || QS.has('nomap')) return null;
    if (riding) return {kind:'summit',lift:riding.l};
    if (mode !== 'free') return null;
    const p=Game.s.p;
    let best=null, dist=34*34;
    for (const l of lifts) {
      if (l.a1-l.a0<=20) continue;
      const b=l.p[0], d=(b[0]-p[0])**2+(b[1]-p[2])**2;
      if(d<dist){best=l;dist=d;}
    }
    return best ? {kind:'board',lift:best} : null;
  };
  const frLiftLabels={
    en:['Ride lift','Go to summit'],pt:['Subir no teleférico','Ir ao topo'],
    ar:['اركب المصعد','إلى القمة'],ja:['リフトに乗る','山頂へ'],
    ko:['리프트 탑승','정상으로'], 'zh-Hant':['乘坐纜車','直接到山頂'],
    'zh-Hans':['乘坐缆车','直接到山顶']
  };
  const frUpdateLift = () => {
    if(!frLiftBtn)return;
    const q=frLiftChoice();
    frLiftBtn.hidden=!q;frLiftBtn.disabled=!q;
    if(!q){delete frLiftBtn.dataset.action;delete frLiftBtn.dataset.lift;return;}
    const label=(frLiftLabels[I18N.lang]||frLiftLabels.en)[q.kind==='summit'?1:0];
    if(frLiftBtn.textContent!==label)frLiftBtn.textContent=label;
    frLiftBtn.dataset.action=q.kind;frLiftBtn.dataset.lift=q.lift.n;
    frLiftBtn.setAttribute('aria-label',label+' · '+q.lift.n);
  };
  const frUseLift = () => {
    const q=frLiftChoice();if(!q)return;
    if(q.kind==='summit')rideEnd(true);
    else {nearLift=q.lift;ride();}
    frUpdateLift();
  };""")
    rep("    mCv = mini.children[0]; hud.appendChild(mini); sizeMini(); addEventListener('resize', sizeMini);",
        """    mCv = mini.children[0]; hud.appendChild(mini); sizeMini(); addEventListener('resize', sizeMini);
    frLiftBtn=document.createElement('button');
    frLiftBtn.id='fr-lift-action';frLiftBtn.type='button';frLiftBtn.hidden=true;frLiftBtn.disabled=true;
    for(const ev of ['pointerdown','pointerup','touchstart','touchend','mousedown','mouseup'])
      frLiftBtn.addEventListener(ev,e=>e.stopPropagation(),{passive:true});
    frLiftBtn.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();frUseLift();frLiftBtn.blur();});
    mini.appendChild(frLiftBtn);""")
    rep("  const tick = () => { if (riding) { const q = AVZ.lift.pos(),",
        "  const tick = () => { frUpdateLift(); if (riding) { const q = AVZ.lift.pos(),")
    rep("    if (!mini && !mount()) return;",
        "    if (!mini && !mount()) return;\\n    frUpdateLift();".replace("\\n","\n"))
    rep("if (nearLift) cap('<b style=\"font-weight:600;color:var(--sun);margin-right:8px\">E</b>坐 '",
        "if (nearLift) cap((frTouch()?'':'<b style=\"font-weight:600;color:var(--sun);margin-right:8px\">E</b>')+'坐 '")
    rep("say('乘坐 ' + nameOf(l.n) + ' · 左右键转头 · 再按 E 直接到山顶', 7);",
        "say('乘坐 ' + nameOf(l.n) + (frTouch()?' · 点缆车按钮直接到山顶':' · 左右键转头 · 再按 E 直接到山顶'), 7);")
    return src
