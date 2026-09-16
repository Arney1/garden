/*! Copyright (c) 2026 Arney Nova. MIT License; see /licenses/MIT.txt. */
/* Graph data and drawing code load only on /graph/. No database or runtime layout. */
(async () => {
  const host = document.getElementById('graph');
  if (!host) return;
  const canvas = host.querySelector('canvas');
  const context = canvas.getContext('2d');
  const status = document.getElementById('graph-status');
  const detail = document.getElementById('graph-detail');
  const search = document.getElementById('graph-search');
  const searchResults = document.getElementById('graph-results');
  const local = document.getElementById('graph-local');
  const isolated = document.getElementById('graph-isolated');
  const labels = document.getElementById('graph-labels');
  let graph;
  try {
    const response = await fetch(host.dataset.source);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    graph = await response.json();
    if (!Array.isArray(graph.nodes) || !Array.isArray(graph.links)) throw new Error('Invalid graph data');
    if (!context) throw new Error('Canvas unavailable');
  } catch (error) {
    status.textContent = 'The graph could not load. Reload to retry, or browse All pages.';
    return;
  }
  const {nodes, links} = graph;
  const neighbors = nodes.map(() => new Set());
  for (const [a, b] of links) { neighbors[a].add(b); neighbors[b].add(a); }
  let selected = -1, hovered = -1, width = 1, height = 1, scale = 1, offsetX = 0, offsetY = 0;
  let visible = new Set(), visibleLinks = [], pending = false;
  const colors = {home:'#98bfa2', tag:'#ba9df0', page:'#8a849c'};
  const radius = i => (2.8 + Math.min(6, Math.sqrt(neighbors[i].size) * .7)) * Math.max(.5, Math.min(1.4, Math.sqrt(scale)));
  const point = n => ({x: n.x * scale + offsetX, y: n.y * scale + offsetY});
  const requestDraw = () => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => { pending = false; draw(); });
  };
  function draw() {
    context.clearRect(0,0,width,height);
    for (const [a,b] of visibleLinks) {
      const active = selected === a || selected === b;
      context.strokeStyle = active ? 'rgba(185,154,224,.65)' : (selected >= 0 ? 'rgba(110,97,130,.10)' : 'rgba(125,110,145,.18)');
      context.lineWidth = active ? 1.25 : .65;
      const p = point(nodes[a]), q = point(nodes[b]);
      context.beginPath(); context.moveTo(p.x,p.y); context.lineTo(q.x,q.y); context.stroke();
    }
    const labelBoxes = [];
    for (const i of visible) {
      const n = nodes[i], p = point(n);
      if (p.x < -50 || p.x > width+50 || p.y < -50 || p.y > height+50) continue;
      const active = selected === i || hovered === i;
      const related = selected < 0 || selected === i || neighbors[selected].has(i);
      context.globalAlpha = related || hovered === i ? 1 : .25;
      context.fillStyle = colors[n.kind] || colors.page;
      context.beginPath(); context.arc(p.x,p.y,radius(i) * (active ? 1.2 : 1),0,Math.PI*2); context.fill();
      if (selected === i) {
        context.strokeStyle = '#e6d9fc'; context.lineWidth = 1.5;
        context.beginPath(); context.arc(p.x,p.y,radius(i)+4,0,Math.PI*2); context.stroke();
      }
      if (active || (labels.checked && related && (scale > .9 || n.kind === 'home' || (neighbors[i].size > 15 && selected < 0) || (selected >= 0 && neighbors[selected].has(i))))) {
        context.font = active ? '600 12px system-ui' : '10px system-ui';
        const title = n.title.length > 43 ? n.title.slice(0,40) + '…' : n.title;
        const box = {x:p.x+radius(i)+5, y:p.y-9, w:context.measureText(title).width+5, h:16};
        if (!active && labelBoxes.some(b=>box.x<b.x+b.w && box.x+box.w>b.x && box.y<b.y+b.h && box.y+box.h>b.y)) continue;
        labelBoxes.push(box);
        context.lineWidth = 4; context.strokeStyle = '#17171b';
        context.strokeText(title,p.x+radius(i)+5,p.y+4);
        context.fillStyle = active ? '#f3eafb' : '#c2b5d1'; context.fillText(title,p.x+radius(i)+5,p.y+4);
      }
    }
    context.globalAlpha = 1;
  }
  function filter() {
    visible = new Set(nodes.map((_,i)=>i).filter(i =>
      (isolated.checked || neighbors[i].size || i === selected) &&
      (!local.checked || selected < 0 || i === selected || neighbors[selected].has(i))));
    visibleLinks = links.filter(([a,b])=>visible.has(a)&&visible.has(b));
    status.textContent = `${visible.size} pages · ${visibleLinks.length} connections`;
  }
  function fit() {
    if (!visible.size) { scale=1; offsetX=width/2; offsetY=height/2; requestDraw(); return; }
    const xs = [...visible].map(i=>nodes[i].x), ys = [...visible].map(i=>nodes[i].y);
    const left=Math.min(...xs), right=Math.max(...xs), top=Math.min(...ys), bottom=Math.max(...ys);
    scale = Math.min(2, Math.max(.03, Math.min((width-80)/Math.max(80,right-left),(height-80)/Math.max(80,bottom-top))));
    offsetX=width/2-(left+right)/2*scale; offsetY=height/2-(top+bottom)/2*scale;
    requestDraw();
  }
  function showDetail() {
    detail.replaceChildren();
    const heading=document.createElement('h2');
    if (selected < 0) {
      heading.textContent='Follow a connection';
      const info=document.createElement('p');
      info.textContent='Select a dot to discover a page and its neighbors. Search above to find a starting point.';
      detail.append(heading,info); return;
    }
    const n=nodes[selected]; heading.textContent=n.title;
    const open=document.createElement('a');open.className='graph-open';open.href=n.url;open.textContent='Open page ↗';
    const caption=document.createElement('p');caption.textContent=`${neighbors[selected].size} connected pages`;
    const list=document.createElement('ul');list.className='graph-neighbors';
    for (const i of [...neighbors[selected]].sort((a,b)=>nodes[a].title.localeCompare(nodes[b].title))) {
      const li=document.createElement('li'),a=document.createElement('a');a.href=nodes[i].url;a.textContent=nodes[i].title;li.append(a);list.append(li);
    }
    detail.append(heading,open,caption,list);
  }
  function select(i,center=false) {
    selected=i;
    filter(); showDetail();
    if (local.checked) fit();
    else if (center && i>=0) { offsetX=width/2-nodes[i].x*scale;offsetY=height/2-nodes[i].y*scale; }
    requestDraw();
  }
  function zoom(factor,x=width/2,y=height/2) {
    const next=Math.max(.03,Math.min(5,scale*factor));
    offsetX=x-(x-offsetX)*(next/scale);offsetY=y-(y-offsetY)*(next/scale);scale=next;requestDraw();
  }
  function hit(x,y) {
    let nearest=-1,distance=Infinity;
    for (const i of visible) { const p=point(nodes[i]);const d=Math.hypot(p.x-x,p.y-y);if(d<Math.max(10,radius(i)+4)&&d<distance){nearest=i;distance=d;} }
    return nearest;
  }
  const position = event => { const r=canvas.getBoundingClientRect();return {x:event.clientX-r.left,y:event.clientY-r.top}; };
  const pointers=new Map();
  let drag=null,pinchDistance=0;
  canvas.addEventListener('pointerdown',event=>{
    if(event.button!==0) return;
    const p=position(event);pointers.set(event.pointerId,p);canvas.setPointerCapture(event.pointerId);
    if(pointers.size===1) drag={id:hit(p.x,p.y),x:p.x,y:p.y,startX:p.x,startY:p.y,moved:false};
    else { const [a,b]=[...pointers.values()];pinchDistance=Math.hypot(a.x-b.x,a.y-b.y);if(drag)drag.moved=true; }
  });
  canvas.addEventListener('pointermove',event=>{
    const p=position(event);
    if(!pointers.has(event.pointerId)){const i=hit(p.x,p.y);if(i!==hovered){hovered=i;canvas.style.cursor=i<0?'grab':'pointer';requestDraw();}return;}
    pointers.set(event.pointerId,p);
    if(pointers.size===2){const [a,b]=[...pointers.values()];const d=Math.hypot(a.x-b.x,a.y-b.y);if(pinchDistance>0)zoom(d/pinchDistance,(a.x+b.x)/2,(a.y+b.y)/2);pinchDistance=d;return;}
    if(!drag)return;
    const dx=p.x-drag.x,dy=p.y-drag.y;
    if(Math.hypot(p.x-drag.startX,p.y-drag.startY)>4)drag.moved=true;
    if(drag.moved){if(drag.id>=0){nodes[drag.id].x+=dx/scale;nodes[drag.id].y+=dy/scale;}else{offsetX+=dx;offsetY+=dy;}}
    drag.x=p.x;drag.y=p.y;requestDraw();
  });
  const release = (event,cancelled=false) => {
    if(!pointers.has(event.pointerId))return;
    pointers.delete(event.pointerId);
    if(!cancelled && !pointers.size && drag && !drag.moved)select(drag.id);
    drag=null;pinchDistance=0;
  };
  canvas.addEventListener('pointerup',event=>release(event));
  canvas.addEventListener('pointercancel',event=>release(event,true));
  canvas.addEventListener('pointerleave',()=>{hovered=-1;requestDraw();});
  canvas.addEventListener('wheel',event=>{event.preventDefault();const p=position(event);zoom(Math.exp(-event.deltaY*.0015),p.x,p.y);},{passive:false});
  canvas.addEventListener('keydown',event=>{
    if(['+','=','-','0','Escape','Enter','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(event.key))event.preventDefault();
    if(event.key==='+'||event.key==='=')zoom(1.3);
    if(event.key==='-')zoom(1/1.3);
    if(event.key==='0')fit();
    if(event.key==='Escape'){local.checked=false;select(-1);}
    if(event.key==='Enter'&&selected>=0)location.assign(nodes[selected].url);
    if(event.key==='ArrowLeft')offsetX+=40;if(event.key==='ArrowRight')offsetX-=40;
    if(event.key==='ArrowUp')offsetY+=40;if(event.key==='ArrowDown')offsetY-=40;
    requestDraw();
  });
  document.getElementById('graph-fit').addEventListener('click',fit);
  document.getElementById('graph-zoom-in').addEventListener('click',()=>zoom(1.3));
  document.getElementById('graph-zoom-out').addEventListener('click',()=>zoom(1/1.3));
  document.getElementById('graph-clear').addEventListener('click',()=>{local.checked=false;search.value='';searchResults.replaceChildren();select(-1);fit();});
  local.addEventListener('change',()=>{filter();fit();});isolated.addEventListener('change',()=>{filter();fit();});labels.addEventListener('change',requestDraw);
  function find() {
    const query=search.value.trim().toLocaleLowerCase();searchResults.replaceChildren();
    if(!query)return;
    const rank = n => n.title.toLocaleLowerCase()===query ? 2 : n.title.toLocaleLowerCase().startsWith(query) ? 1 : 0;
    const matches=nodes.map((n,i)=>({n,i})).filter(({n})=>n.title.toLocaleLowerCase().includes(query)).sort((a,b)=>rank(b.n)-rank(a.n)||a.n.title.localeCompare(b.n.title)).slice(0,12);
    for(const {n,i} of matches){const li=document.createElement('li'),button=document.createElement('button');button.type='button';button.textContent=n.title;button.addEventListener('click',()=>{select(i,true);searchResults.replaceChildren();search.value=n.title;});li.append(button);searchResults.append(li);}
    if(!matches.length){const li=document.createElement('li');li.textContent='No matching pages';searchResults.append(li);}
  }
  search.addEventListener('input',find);
  search.addEventListener('keydown',event=>{if(event.key==='Enter'){const first=searchResults.querySelector('button');if(first){event.preventDefault();first.click();}}});
  let initialized=false;
  new ResizeObserver(()=>{
    const bounds=canvas.parentElement.getBoundingClientRect();
    const oldWidth=width,oldHeight=height;width=bounds.width;height=bounds.height;
    const ratio=Math.min(2,window.devicePixelRatio||1);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);context.setTransform(ratio,0,0,ratio,0,0);
    if(!initialized){initialized=true;fit();}else{offsetX+=(width-oldWidth)/2;offsetY+=(height-oldHeight)/2;requestDraw();}
  }).observe(canvas.parentElement);
  const start=new URLSearchParams(location.search).get('page');
  if(start){selected=nodes.findIndex(n=>n.id===start||n.title.toLocaleLowerCase()===start.toLocaleLowerCase());local.checked=selected>=0;}
  filter();showDetail();
})();
